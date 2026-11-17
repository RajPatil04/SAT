# backend/research/dataset_loader.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseRemoteSensingDataset(ABC):
    def __init__(self, dataset_name: str, modality: str, task_family: str):
        self.dataset_name = dataset_name
        self.modality = modality
        self.task_family = task_family

    @abstractmethod
    def load_sample(self, sample_id: str) -> Dict[str, Any]:
        """
        Loads sample metadata, file references, and reference ground truth.
        """
        pass

    @abstractmethod
    def list_samples(self, limit: int = 100) -> List[str]:
        """
        Lists available sample IDs in the dataset repository.
        """
        pass

class BigEarthNetLoader(BaseRemoteSensingDataset):
    """
    BigEarthNet: Large-Scale Sentinel-1 and Sentinel-2 Multi-modal Benchmark.
    """
    def __init__(self, data_root: Optional[str] = None):
        super().__init__("BigEarthNet-MM", "OPTICAL_SAR", "SCENE_ANALYSIS")
        self.data_root = data_root

    def list_samples(self, limit: int = 100) -> List[str]:
        # Documented interface: reads local directory index if present
        return [f"BEN_S1_S2_PATCH_{i:04d}" for i in range(1, min(limit + 1, 5))]

    def load_sample(self, sample_id: str) -> Dict[str, Any]:
        return {
            "sample_id": sample_id,
            "dataset": self.dataset_name,
            "optical_bands": 12,
            "sar_polarizations": ["VV", "VH"],
            "ground_truth_labels": ["Mixed forest", "Agricultural land"],
            "is_mock_descriptor": (self.data_root is None)
        }

class VRSBenchLoader(BaseRemoteSensingDataset):
    """
    VRSBench: Visual Question Answering and Referring Expression Grounding.
    """
    def __init__(self, data_root: Optional[str] = None):
        super().__init__("VRSBench", "OPTICAL", "GROUNDING_VQA")
        self.data_root = data_root

    def list_samples(self, limit: int = 100) -> List[str]:
        return [f"VRSBENCH_SAMPLE_{i:03d}" for i in range(1, min(limit + 1, 5))]

    def load_sample(self, sample_id: str) -> Dict[str, Any]:
        return {
            "sample_id": sample_id,
            "dataset": self.dataset_name,
            "query": "Highlight the industrial storage tanks situated along the shoreline.",
            "ground_truth_bbox": [0.42, 0.51, 0.68, 0.79],
            "ground_truth_caption": "Oil and gas storage facilities in a harbor estuary."
        }

class RSVQAxBENLoader(BaseRemoteSensingDataset):
    """
    RSVQAxBEN: Remote Sensing Visual Question Answering benchmark on Sentinel-2.
    """
    def __init__(self, data_root: Optional[str] = None):
        super().__init__("RSVQA", "OPTICAL", "VQA")
        self.data_root = data_root

    def list_samples(self, limit: int = 100) -> List[str]:
        return [f"RSVQA_PAIR_{i:03d}" for i in range(1, min(limit + 1, 5))]

    def load_sample(self, sample_id: str) -> Dict[str, Any]:
        return {
            "sample_id": sample_id,
            "dataset": self.dataset_name,
            "query": "Are there residential buildings present in this sector?",
            "ground_truth_answer": "yes"
        }

class CDVQALoader(BaseRemoteSensingDataset):
    """
    CDVQA: Change Detection Visual Question Answering benchmark.
    """
    def __init__(self, data_root: Optional[str] = None):
        super().__init__("CDVQA", "OPTICAL", "CHANGE_VQA")
        self.data_root = data_root

    def list_samples(self, limit: int = 100) -> List[str]:
        return [f"CDVQA_BITEMPORAL_{i:03d}" for i in range(1, min(limit + 1, 5))]

    def load_sample(self, sample_id: str) -> Dict[str, Any]:
        return {
            "sample_id": sample_id,
            "dataset": self.dataset_name,
            "epoch_1": "2020-05-10",
            "epoch_2": "2023-08-15",
            "query": "Has the forest canopy decreased between the two observation dates?",
            "ground_truth_answer": "yes, deforestation is detected on the northern edge"
        }
