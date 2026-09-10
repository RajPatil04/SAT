"""
Sample loader for SatQuery AI local demo mode.
Loads predefined datasets and verified analytical results without requiring internet access.
"""
import os
import json
from typing import Dict, Any, List

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")

class SampleLoader:
    @staticmethod
    def get_sample(mode: str) -> Dict[str, Any]:
        """Loads verified sample data for a specific mode."""
        mode_mapping = {
            "single_image": "single_image",
            "single": "single_image",
            "bi_temporal": "bi_temporal",
            "temporal": "bi_temporal",
            "optical_sar": "optical_sar",
            "cross_modal": "optical_sar"
        }
        sub_folder = mode_mapping.get(mode.lower().replace("-", "_").replace(" ", "_"), "single_image")
        json_path = os.path.join(DATA_DIR, sub_folder, "result.json")
        
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Sample data for {mode} not found at {json_path}")
            
        with open(json_path, "r") as f:
            data = json.load(f)
            
        # Add relative URL paths for frontend consumption
        data["mode_id"] = sub_folder
        data["assets_base"] = f"/data/samples/{sub_folder}"
        return data

    @staticmethod
    def list_all_samples() -> List[Dict[str, Any]]:
        """Returns metadata for all available predefined gallery samples."""
        modes = ["single_image", "bi_temporal", "optical_sar"]
        results = []
        for m in modes:
            try:
                results.append(SampleLoader.get_sample(m))
            except Exception:
                pass
        return results
