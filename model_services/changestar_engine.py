# model_services/changestar_engine.py
import os
import sys
import time
import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Union

import torch
import torch.nn as nn
from PIL import Image
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ChangeStarEngine")

# Path constants
BASE_DIR = Path(__file__).resolve().parent.parent
CHANGEN_DIR = Path(__file__).resolve().parent / "Changen"
WEIGHTS_DIR = BASE_DIR / "pretrained_weights"
DEFAULT_WEIGHTS_PATH = WEIGHTS_DIR / "changestar1x96_r18_ft_levircd.pth"
WEIGHTS_URL = "https://github.com/Z-Zheng/Changen/releases/download/v0.1/changestar1x96_r18_ft_levircd.pth"

# Ensure Changen directory is on sys.path for internal imports
if str(CHANGEN_DIR) not in sys.path:
    sys.path.insert(0, str(CHANGEN_DIR))
CONFIGS_DIR = CHANGEN_DIR / "configs"
if str(CONFIGS_DIR) not in sys.path:
    sys.path.insert(0, str(CONFIGS_DIR))


def ensure_weights_available(weights_path: Path = DEFAULT_WEIGHTS_PATH) -> Path:
    """Ensure pretrained weights are downloaded and accessible locally."""
    weights_path.parent.mkdir(parents=True, exist_ok=True)
    if weights_path.exists() and weights_path.stat().st_size > 10_000_000:
        logger.info(f"ChangeStar weights already present at {weights_path}")
        return weights_path

    logger.info(f"Downloading ChangeStar weights to {weights_path} from {WEIGHTS_URL}...")
    import urllib.request
    urllib.request.urlretrieve(WEIGHTS_URL, str(weights_path))
    logger.info(f"Download complete: {weights_path.stat().st_size} bytes")
    return weights_path


class ChangeStarEngine:
    """
    Inference Engine for official pretrained ChangeStar (ResNet-18 backbone, LEVIR-CD fine-tuned).
    Follows official 6-channel input convention: [B, 6, H, W] concatenating T1 and T2 RGB images.
    """
    _instance: Optional["ChangeStarEngine"] = None

    def __init__(self, weights_path: Optional[str] = None, device: Optional[str] = None):
        self.device = torch.device(
            device if device else ("cuda:0" if torch.cuda.is_available() else "cpu")
        )
        self.weights_path = Path(weights_path) if weights_path else DEFAULT_WEIGHTS_PATH
        self.model: Optional[nn.Module] = None
        self._load_model()

    @classmethod
    def get_instance(cls, weights_path: Optional[str] = None, device: Optional[str] = None) -> "ChangeStarEngine":
        if cls._instance is None:
            cls._instance = cls(weights_path=weights_path, device=device)
        return cls._instance

    def _load_model(self):
        """Loads and initializes the ChangeStar model with LEVIR-CD pretrained weights."""
        logger.info(f"Initializing ChangeStar with device: {self.device}")
        ensure_weights_available(self.weights_path)

        # Import ever and Changen architecture
        import ever as er
        import changestar_1x96 as cstar

        # Import official ResNet-18 config
        try:
            from cstar_r18_farseg_d96 import config
            model_config = config["model"]
        except ImportError:
            # Fallback if configs dir not on path
            cfg_path = CHANGEN_DIR / "configs" / "cstar_r18_farseg_d96.py"
            import importlib.util
            spec = importlib.util.spec_from_file_location("cstar_r18_config", str(cfg_path))
            cfg_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cfg_module)
            model_config = cfg_module.config["model"]

        # Build official model architecture
        self.model = er.builder.make_model(model_config)

        # Load weights
        checkpoint = torch.load(str(self.weights_path), map_location="cpu", weights_only=False)
        if isinstance(checkpoint, dict):
            if "model" in checkpoint:
                state_dict = checkpoint["model"]
            elif "state_dict" in checkpoint:
                state_dict = checkpoint["state_dict"]
            else:
                state_dict = checkpoint
        else:
            state_dict = checkpoint

        # Clean prefix if any
        cleaned_weights = {}
        for k, v in state_dict.items():
            if k.startswith("module."):
                cleaned_weights[k[len("module."):]] = v
            else:
                cleaned_weights[k] = v

        self.model.load_state_dict(cleaned_weights, strict=True)
        self.model.to(self.device)
        self.model.eval()
        logger.info("ChangeStar ResNet-18 LEVIR-CD model successfully loaded and moved to eval mode.")

    def preprocess(
        self,
        t1_input: Union[str, Path, Image.Image, np.ndarray],
        t2_input: Union[str, Path, Image.Image, np.ndarray],
        target_size: Optional[Tuple[int, int]] = None
    ) -> Tuple[torch.Tensor, Tuple[int, int]]:
        """
        Loads and consistently preprocesses two temporal images:
        - Ensures RGB format
        - Validates dimensions & resizes/aligns spatial extent
        - Pads or ensures spatial dimensions are divisible by 32 (FPN stride)
        - Normalizes using standard ImageNet mean and std
        - Concatenates into 6-channel tensor [1, 6, H, W]
        """
        def to_pil(img_input):
            if isinstance(img_input, (str, Path)):
                return Image.open(str(img_input)).convert("RGB")
            elif isinstance(img_input, np.ndarray):
                if img_input.ndim == 2:
                    return Image.fromarray(img_input).convert("RGB")
                elif img_input.shape[2] == 1:
                    return Image.fromarray(img_input[:, :, 0]).convert("RGB")
                elif img_input.shape[0] == 3: # CHW format
                    return Image.fromarray(np.transpose(img_input, (1, 2, 0))).convert("RGB")
                return Image.fromarray(img_input).convert("RGB")
            elif isinstance(img_input, Image.Image):
                return img_input.convert("RGB")
            raise ValueError(f"Unsupported image input type: {type(img_input)}")

        img1 = to_pil(t1_input)
        img2 = to_pil(t2_input)

        # Dimension validation: align to target size or match T1
        if target_size:
            w, h = target_size
            img1 = img1.resize((w, h), Image.Resampling.BILINEAR)
            img2 = img2.resize((w, h), Image.Resampling.BILINEAR)
        elif img1.size != img2.size:
            logger.warning(f"Dimension mismatch between T1 {img1.size} and T2 {img2.size}. Resizing T2 to match T1.")
            img2 = img2.resize(img1.size, Image.Resampling.BILINEAR)

        # Ensure spatial dimensions are multiples of 32 (ResNet + FPN requirements)
        w, h = img1.size
        pad_w = (32 - (w % 32)) % 32
        pad_h = (32 - (h % 32)) % 32
        if pad_w != 0 or pad_h != 0:
            target_w, target_h = w + pad_w, h + pad_h
            img1 = img1.resize((target_w, target_h), Image.Resampling.BILINEAR)
            img2 = img2.resize((target_w, target_h), Image.Resampling.BILINEAR)

        orig_dims = (img1.height, img1.width)

        # Convert to numpy float32 [H, W, 3] -> [0, 1]
        arr1 = np.array(img1, dtype=np.float32) / 255.0
        arr2 = np.array(img2, dtype=np.float32) / 255.0

        # Standard ImageNet normalization expected by ResNet backbone
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

        arr1 = (arr1 - mean) / std
        arr2 = (arr2 - mean) / std

        # Transpose to [3, H, W]
        t1_tensor = torch.from_numpy(arr1.transpose(2, 0, 1))
        t2_tensor = torch.from_numpy(arr2.transpose(2, 0, 1))

        # 6-channel concatenation [1, 6, H, W]
        bi_tensor = torch.cat([t1_tensor, t2_tensor], dim=0).unsqueeze(0)
        return bi_tensor, orig_dims

    def predict(
        self,
        t1_input: Union[str, Path, Image.Image, np.ndarray],
        t2_input: Union[str, Path, Image.Image, np.ndarray],
        threshold: float = 0.5,
        target_size: Optional[Tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """
        Executes bi-temporal change prediction.
        Returns prediction mask, change percentage, metadata, and encoded visual mask.
        """
        start_time = time.perf_counter()

        bi_tensor, (h, w) = self.preprocess(t1_input, t2_input, target_size=target_size)
        bi_tensor = bi_tensor.to(self.device)

        with torch.inference_mode():
            outputs = self.model(bi_tensor)
            # Output dictionary contains 'change_prediction' with sigmoid probabilities [B, 1, H, W]
            change_prob = outputs["change_prediction"]
            prob_map = change_prob.squeeze(0).squeeze(0).cpu().numpy()

        binary_mask = (prob_map >= threshold).astype(np.uint8) * 255
        changed_pixels = int(np.count_nonzero(binary_mask))
        total_pixels = int(binary_mask.size)
        change_percentage = round((changed_pixels / total_pixels) * 100.0, 4)
        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Convert binary mask to PNG bytes and base64
        mask_pil = Image.fromarray(binary_mask, mode="L")
        buf = BytesIO()
        mask_pil.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        base64_str = base64.b64encode(png_bytes).decode("utf-8")

        return {
            "model": "ChangeStar-1x96 (ResNet-18, LEVIR-CD)",
            "device": str(self.device),
            "input_shape": list(bi_tensor.shape),
            "output_dimensions": {"height": h, "width": w},
            "threshold": threshold,
            "changed_pixels": changed_pixels,
            "total_pixels": total_pixels,
            "change_percentage": change_percentage,
            "inference_time_ms": latency_ms,
            "change_mask_base64": f"data:image/png;base64,{base64_str}",
            "mean_change_probability": float(np.mean(prob_map)),
            "max_change_probability": float(np.max(prob_map))
        }
