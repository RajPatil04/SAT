# backend/router/query_analyzer.py
import re
from typing import Dict, Any, List, Optional
from backend.router.schemas import StructuredTaskSpecification, ModalityType, TaskType

# Keyword lexicon for remote-sensing query understanding
GROUNDING_KEYWORDS = {
    "highlight", "locate", "localize", "bounding box", "bbox", "segment",
    "pinpoint", "where is", "where are", "draw a box", "outline", "delineate"
}

CHANGE_KEYWORDS = {
    "change", "changed", "changes", "difference", "differ", "diff",
    "increased", "decreased", "expanded", "shrunk", "disappeared", "newly built",
    "between these two", "between dates", "over time", "before and after"
}

CHANGE_VQA_KEYWORDS = {
    "has the", "have the", "did the", "is there any change",
    "how much has", "why did", "what kind of change", "increased or decreased"
}

OPTICAL_SAR_KEYWORDS = {
    "optical and sar", "sar and optical", "optical + sar", "radar and optical",
    "sentinel-1 and sentinel-2", "s1 and s2", "together to identify",
    "use both images", "fused", "fusion", "cross-modal", "using both"
}

CAPTIONING_KEYWORDS = {
    "describe", "description", "caption", "summarize", "overview of the scene",
    "give a summary", "briefly describe"
}

OBJECT_KEYWORDS = {
    "objects present", "what objects", "how many", "count", "vehicles",
    "airplanes", "aircraft", "ships", "vessels", "buildings", "storage tanks",
    "tanks", "infrastructure"
}

SCENE_KEYWORDS = {
    "land cover", "land-cover", "land use", "landuse", "scene type",
    "terrain", "environment", "urban", "rural", "forest", "water body",
    "classification", "scene analysis"
}

class QueryAnalysis:
    def __init__(self, query: str):
        self.raw_query = query.strip()
        self.normalized_query = query.lower().strip()
        self.tokens = set(re.findall(r'\b\w+\b', self.normalized_query))

    def analyze(self) -> Dict[str, Any]:
        """
        Extracts semantic tokens, task cues, and intents from user query.
        """
        has_grounding = any(kw in self.normalized_query for kw in GROUNDING_KEYWORDS)
        has_change = any(kw in self.normalized_query for kw in CHANGE_KEYWORDS)
        has_change_vqa = has_change and any(kw in self.normalized_query for kw in CHANGE_VQA_KEYWORDS)
        has_optical_sar = any(kw in self.normalized_query for kw in OPTICAL_SAR_KEYWORDS)
        has_caption = any(kw in self.normalized_query for kw in CAPTIONING_KEYWORDS)
        has_object = any(kw in self.normalized_query for kw in OBJECT_KEYWORDS)
        has_scene = any(kw in self.normalized_query for kw in SCENE_KEYWORDS)

        # Detect specific entities or targets
        target_entities = []
        for entity in ["water body", "river", "lake", "ocean", "airport", "runway", "building", "road", "vegetation", "forest", "crop"]:
            if entity in self.normalized_query:
                target_entities.append(entity)

        return {
            "query": self.raw_query,
            "has_grounding_cue": has_grounding,
            "has_change_cue": has_change,
            "has_change_vqa_cue": has_change_vqa,
            "has_optical_sar_cue": has_optical_sar,
            "has_caption_cue": has_caption,
            "has_object_cue": has_object,
            "has_scene_cue": has_scene,
            "target_entities": target_entities,
            "tokens": list(self.tokens)
        }

class QueryAnalyzer:
    @staticmethod
    def analyze_query(query: str) -> Dict[str, Any]:
        analyzer = QueryAnalysis(query)
        return analyzer.analyze()

    @staticmethod
    def generate_task_specification(query: str, num_observations: Optional[int] = None) -> StructuredTaskSpecification:
        """
        Stage 1: Query Interpretation (Paper Section III-C & Section 6 Stage 1).
        Converts the user's natural-language question into an explicit, structured task specification.
        """
        analysis = QueryAnalyzer.analyze_query(query)
        q_lower = (query or "").lower().strip()

        # Check for ambiguity
        is_ambiguous = False
        ambiguity_reason = None
        if len(q_lower) < 4 or q_lower in ("?", "analyze", "test", "look", "what", "what is this"):
            is_ambiguous = True
            ambiguity_reason = f"Query '{query}' is insufficiently specified to determine a targeted remote-sensing task."

        target = analysis["target_entities"][0] if analysis["target_entities"] else None

        # Determine task, observations, and modality
        if analysis["has_optical_sar_cue"]:
            task = "optical_sar_analysis"
            req_obs = 2
            modality = ModalityType.OPTICAL_SAR
            temp_comp = False
            spatial_ev = False
            area_meas = False
            fusion = True
        elif analysis["has_change_vqa_cue"]:
            task = "change_vqa"
            req_obs = 2
            modality = ModalityType.OPTICAL
            temp_comp = True
            spatial_ev = True
            area_meas = any(kw in q_lower for kw in ["how much", "percentage", "area", "extent"])
            fusion = False
        elif analysis["has_change_cue"]:
            task = "bi_temporal_change_detection"
            req_obs = 2
            modality = ModalityType.OPTICAL
            temp_comp = True
            spatial_ev = True
            area_meas = any(kw in q_lower for kw in ["how much", "percentage", "area", "extent"])
            fusion = False
        elif analysis["has_grounding_cue"]:
            task = "visual_grounding"
            req_obs = 1
            modality = ModalityType.OPTICAL
            temp_comp = False
            spatial_ev = True
            area_meas = False
            fusion = False
        elif analysis["has_caption_cue"]:
            task = "captioning"
            req_obs = 1
            modality = ModalityType.OPTICAL
            temp_comp = False
            spatial_ev = False
            area_meas = False
            fusion = False
        elif analysis["has_object_cue"] or analysis["has_scene_cue"]:
            task = "scene_understanding"
            req_obs = 1
            modality = ModalityType.OPTICAL
            temp_comp = False
            spatial_ev = False
            area_meas = False
            fusion = False
        else:
            task = "visual_question_answering"
            req_obs = 1
            modality = ModalityType.OPTICAL
            temp_comp = False
            spatial_ev = False
            area_meas = False
            fusion = False

        if target is None:
            if "built-up" in q_lower or "built up" in q_lower or "building" in q_lower or "structure" in q_lower:
                target = "built_up_area"
            elif "water" in q_lower or "river" in q_lower or "lake" in q_lower:
                target = "water_body"
            elif "tree" in q_lower or "vegetation" in q_lower or "forest" in q_lower:
                target = "vegetation"

        return StructuredTaskSpecification(
            task=task,
            target=target,
            required_observations=req_obs,
            expected_modality=modality,
            temporal_comparison=temp_comp,
            requires_spatial_evidence=spatial_ev,
            requires_area_measurement=area_meas,
            requires_cross_modal_fusion=fusion,
            is_ambiguous=is_ambiguous,
            ambiguity_reason=ambiguity_reason
        )
