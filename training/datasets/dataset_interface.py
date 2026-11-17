# training/datasets/dataset_interface.py
"""
Dataset Interface & PyTorch Dataset Abstraction for Remote-Sensing VLM Adaptation.
"""
from typing import Dict, Any, List, Optional
import os

try:
    from torch.utils.data import Dataset
except ImportError:
    class Dataset:
        pass

class RemoteSensingVLMDataset(Dataset):
    """
    Unified Dataset Interface supporting:
    - Single-image VQA / Captioning (RSVQA, VRSBench)
    - Bi-temporal Change VQA (CDVQA)
    - Multimodal Optical-SAR Fusion (BigEarthNet-MM)
    """
    def __init__(self, manifest_file: str, data_root: str, task: str = "VQA"):
        self.manifest_file = manifest_file
        self.data_root = data_root
        self.task = task
        self.samples: List[Dict[str, Any]] = []
        self._load_manifest()

    def _load_manifest(self):
        if not os.path.exists(self.manifest_file):
            # Fallback to dummy template manifest for interface specification
            self.samples = [
                {
                    "sample_id": "sample_001",
                    "image_paths": ["sample_001.png"],
                    "query": "Describe the land cover in this scene.",
                    "target_answer": "Dense urban structures surrounded by agricultural fields."
                }
            ]
            return

        import json
        with open(self.manifest_file, "r", encoding="utf-8") as f:
            self.samples = json.load(f)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        item = self.samples[idx]
        return {
            "sample_id": item.get("sample_id"),
            "image_paths": [os.path.join(self.data_root, p) for p in item.get("image_paths", [])],
            "query": item.get("query"),
            "target_answer": item.get("target_answer"),
            "grounding_bbox": item.get("grounding_bbox")
        }
