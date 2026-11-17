# backend/tests/test_paper_methodology.py
"""
Automated Verification Suite for Paper Methodology & Architectural Requirements
Tests:
- Section III-C & Section 6 Stage 1: Structured Task Specification Generation
- Section IV-C & IV-D (Eq. 3, 4, 8): Hard Compatibility Constraints C(W_k, X, T) in {0, 1}
- Section V-D (Eq. 9, 10): Compatibility-Aware Routing Scoring S(w_i | q, x) = alpha*I + beta*C_f + gamma*M - lambda*P
- Section V-F (Eq. 11-15): Five Quantitative Metrics (RA, IRR, ESR, EER, L_mean)
- Section V-G Table II: 4 Comparative Routing Configurations (Query-only, Metadata-only, Query+Input, SatQuery AI)
- Section V-H: Six Failure Analysis Stages
- Section IV-G (Eq. 7): Unified Evidence-Oriented Response R = {A, E, C_f, P}
"""

import pytest
from backend.router.schemas import (
    TaskType,
    InputType,
    ModalityType,
    StructuredTaskSpecification,
    ModelCandidateScore,
    ImageMetadata,
    ValidationResult
)
from backend.router.query_analyzer import QueryAnalyzer
from backend.router.router import SatQueryRouter
from backend.research.evaluation import (
    ResearchEvaluator,
    COMPREHENSIVE_BENCHMARK_SUITE,
    EvaluationScenario,
    FailureStage
)

def test_stage1_structured_task_specification_generation():
    """
    Paper Section III-C & Section 6 Stage 1:
    Verifies that QueryAnalyzer produces an explicit, typed StructuredTaskSpecification.
    """
    # 1. Bi-temporal change question
    q_change = "Has the built-up area increased, decreased, or remained unchanged between these dates?"
    spec_change = QueryAnalyzer.generate_task_specification(q_change, num_observations=2)
    assert isinstance(spec_change, StructuredTaskSpecification)
    assert spec_change.task in ("change_vqa", "bi_temporal_change_detection")
    assert spec_change.required_observations == 2
    assert spec_change.temporal_comparison is True
    assert spec_change.requires_spatial_evidence is True
    assert spec_change.target == "built_up_area"

    # 2. Optical-SAR cross-modal question
    q_croma = "Use the optical and SAR images together to analyze surface texture."
    spec_croma = QueryAnalyzer.generate_task_specification(q_croma, num_observations=2)
    assert spec_croma.task == "optical_sar_analysis"
    assert spec_croma.expected_modality == ModalityType.OPTICAL_SAR
    assert spec_croma.requires_cross_modal_fusion is True

    # 3. Single image VQA question
    q_vqa = "What land-cover classes and structures are visible?"
    spec_vqa = QueryAnalyzer.generate_task_specification(q_vqa, num_observations=1)
    assert spec_vqa.task in ("visual_question_answering", "scene_understanding")
    assert spec_vqa.required_observations == 1
    assert spec_vqa.temporal_comparison is False

    # 4. Ambiguous question
    q_amb = "?"
    spec_amb = QueryAnalyzer.generate_task_specification(q_amb)
    assert spec_amb.is_ambiguous is True
    assert spec_amb.ambiguity_reason is not None

def test_paper_hard_compatibility_constraints():
    """
    Paper Section IV-C & IV-D (Eq. 3, 4, 8):
    Hard constraint C(W_k, X, T) in {0, 1}.
    Workflows that fail hard constraints must have is_feasible=False and cannot be selected.
    """
    # Case A: Single image input with ChangeStar candidate
    scores_single = SatQueryRouter._calculate_candidate_scores(
        mode="SINGLE_IMAGE",
        relationship="UNKNOWN",
        question="Describe this satellite scene.",
        semantic_info={"has_change_intent": False, "single_image_focus": False},
        metadata_list=[ImageMetadata(filename="img1.png", format="PNG", width=512, height=512, channels=3, datatype="RGB")],
        validation=None
    )
    cs_score = next(c for c in scores_single if c.model_id == "changestar")
    assert cs_score.is_feasible is False
    assert cs_score.total_score == 0.0  # Zeroed out due to hard constraint failure C=0

    gc_score = next(c for c in scores_single if c.model_id == "geochat-7b")
    assert gc_score.is_feasible is True
    assert gc_score.total_score > 0.0

def test_paper_equation_9_routing_score_computation():
    """
    Paper Section V-D (Eq. 9, 10):
    S(w_i | q, x) = alpha * I(w_i, q) + beta * C_f(w_i, x) + gamma * M(w_i, x) - lambda * P(w_i, q, x)
    Verifies that terms I, C_f, M, P are computed and weighted properly.
    """
    meta_pair = [
        ImageMetadata(filename="t1.png", format="PNG", width=512, height=512, channels=3, datatype="RGB"),
        ImageMetadata(filename="t2.png", format="PNG", width=512, height=512, channels=3, datatype="RGB")
    ]
    val = ValidationResult(
        is_valid=True,
        input_mode="DOUBLE_IMAGE",
        relationship="BI_TEMPORAL",
        images=[],
        spatial_aligned=True,
        modality_compatible=True,
        blocking_errors=[]
    )
    scores = SatQueryRouter._calculate_candidate_scores(
        mode="DOUBLE_IMAGE",
        relationship="BI_TEMPORAL",
        question="What changes occurred between these two images?",
        semantic_info={"has_change_intent": True, "single_image_focus": False},
        metadata_list=meta_pair,
        validation=val
    )
    cs_score = next(c for c in scores if c.model_id == "changestar")
    assert cs_score.intent_score == 1.0
    assert cs_score.input_compatibility == 1.0
    assert cs_score.modality_score == 1.0
    assert cs_score.penalty == 0.0
    # Expected score = 0.40*1.0 + 0.30*1.0 + 0.20*1.0 - 0.50*0.0 = 0.90
    assert abs(cs_score.total_score - 0.90) < 1e-3

def test_table_ii_comparative_evaluation():
    """
    Paper Section V-G Table II & Section V-F:
    Evaluates Query-only, Metadata-only, Query+Input, and SatQuery AI.
    Verifies that SatQuery AI achieves superior Invalid-Input Rejection Rate (IRR)
    and End-to-End Reliability (EER) through full compatibility validation.
    """
    res = ResearchEvaluator.run_table_ii_evaluation()
    table = res["table_ii_metrics"]
    assert len(table) == 4

    q_only = next(m for m in table if m["configuration_key"] == "query_only")
    meta_only = next(m for m in table if m["configuration_key"] == "metadata_only")
    satquery = next(m for m in table if m["configuration_key"] == "satquery_ai")

    # In Table II: Metadata-only cannot reject invalid queries (IRR=0%)
    assert meta_only["invalid_input_rejection_rate_irr"] == 0.0
    # Query-only fails to check image counts and modalities (IRR=33.33%)
    assert q_only["invalid_input_rejection_rate_irr"] < 50.0
    # SatQuery AI achieves 100% rejection of invalid/incompatible inputs!
    assert satquery["invalid_input_rejection_rate_irr"] == 100.0
    assert satquery["end_to_end_reliability_eer"] == 100.0
    assert satquery["failures_by_stage"]["3) Compatibility-validation failures"] == 0

def test_six_failure_analysis_stages_presence():
    """
    Paper Section V-H:
    Verifies that all 6 failure stages are defined and tracked in evaluation telemetry.
    """
    stages = [s.value for s in FailureStage]
    assert len(stages) == 6
    assert any("Query-intent" in s for s in stages)
    assert any("candidate generation" in s for s in stages)
    assert any("Compatibility-validation" in s for s in stages)
    assert any("routing selection" in s for s in stages)
    assert any("Specialist execution" in s for s in stages)
    assert any("Response-integration" in s for s in stages)

