# backend/preprocessing/base_preprocessor.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from PIL import Image

class BasePreprocessor(ABC):
    @abstractmethod
    def preprocess(self, file_paths: List[str], **kwargs) -> Dict[str, Any]:
        """
        Preprocesses raw satellite/remote-sensing input files into model-ready tensors/images.
        """
        pass
