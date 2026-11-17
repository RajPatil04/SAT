# backend/config/endpoint_config.py
"""
Central Model Endpoint Configuration Loader for SatQuery AI.
Section 3: Authoritative configuration module for model_endpoints.yaml.

Rules:
1. model_endpoints.yaml is the single authoritative configuration source for all service endpoints.
2. All model adapters and routing registries read settings through this module.
3. No hardcoded GeoChat URLs in frontend or adapter logic.
4. Credentials/API keys are read exclusively from environment variables, never stored in YAML.
5. Provides validation on startup and dynamic reload capability for testing.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from pydantic import BaseModel, Field

logger = logging.getLogger("SatQueryConfig")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
YAML_PATH = BASE_DIR / "backend" / "config" / "model_endpoints.yaml"

class ServiceConfig(BaseModel):
    base_url: str = ""
    api_type: str = "rest"  # "rest" or "gradio"
    api_name: Optional[str] = "predict"
    analyze_path: Optional[str] = "/predict"
    timeout_seconds: int = 180
    enabled: bool = True
    api_key_env_var: Optional[str] = None

    def is_configured(self) -> bool:
        """
        Returns True only if the service is enabled, has a non-empty base_url,
        and is NOT the placeholder 'https://REPLACE-WITH-ACTUAL-GEOCHAT-ENDPOINT'.
        """
        if not self.enabled:
            return False
        if not self.base_url or not self.base_url.strip():
            return False
        clean_url = self.base_url.strip()
        if "REPLACE-WITH" in clean_url or "PLACEHOLDER" in clean_url.upper():
            return False
        return True

    def get_api_key(self) -> Optional[str]:
        """
        Safely retrieves the service API key from environment variables.
        Credentials are never stored in YAML or printed in logs.
        """
        if self.api_key_env_var:
            return os.getenv(self.api_key_env_var)
        # Default fallback convention based on common service names
        return None

    def get_endpoint_url(self) -> str:
        """Returns the fully qualified target endpoint URL."""
        base = self.base_url.rstrip("/")
        if self.api_type == "gradio":
            endpoint = self.api_name or "predict"
            return f"{base}/api/{endpoint}" if not base.endswith("/api") else f"{base}/{endpoint}"
        else:
            path = (self.analyze_path or "/predict").lstrip("/")
            return f"{base}/{path}"

class RoutingConfig(BaseModel):
    default_strategy: str = "query_driven"
    enable_cross_model_reasoning: bool = True

class InferenceConfig(BaseModel):
    allow_mock_models: bool = False
    verify_service_before_inference: bool = True

class LanguageGenerationConfig(BaseModel):
    provider: str = "none"  # "none", "openai", "anthropic", "gemini", "ollama", "rest"
    base_url: str = ""
    model: str = ""
    api_key_env_var: Optional[str] = "LLM_API_KEY"
    timeout_seconds: int = 30
    enabled: bool = False

    def is_configured(self) -> bool:
        if not self.enabled:
            return False
        prov = self.provider.strip().lower()
        if prov in ("none", ""):
            return False
        if prov in ("ollama", "rest"):
            return bool(self.base_url and self.base_url.strip())
        if self.api_key_env_var and os.getenv(self.api_key_env_var):
            return True
        if self.base_url and self.base_url.strip():
            return True
        return False

    def get_api_key(self) -> Optional[str]:
        if self.api_key_env_var:
            return os.getenv(self.api_key_env_var)
        return None

class EndpointsConfiguration(BaseModel):
    services: Dict[str, ServiceConfig] = Field(default_factory=dict)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    inference: InferenceConfig = Field(default_factory=InferenceConfig)
    language_generation: LanguageGenerationConfig = Field(default_factory=LanguageGenerationConfig)

    @classmethod
    def load_from_file(cls, yaml_path: Optional[Path] = None) -> "EndpointsConfiguration":
        target_path = yaml_path or YAML_PATH
        if not target_path.exists():
            logger.warning(f"Configuration file {target_path} not found. Using defaults.")
            return cls()

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        except Exception as e:
            logger.error(f"Failed to parse {target_path}: {e}. Falling back to default configuration.")
            return cls()

    def get_service(self, name: str) -> ServiceConfig:
        """
        Retrieves the service configuration for a named model service
        (e.g. 'geochat', 'changestar', 'croma', 'grounding').
        Returns a disabled default ServiceConfig if not found.
        """
        normalized_name = name.lower().replace("-7b", "").replace("-", "")
        for key, service in self.services.items():
            if key.lower().replace("-7b", "").replace("-", "") == normalized_name:
                return service
        return ServiceConfig(base_url="", enabled=False)

    def validate_configuration(self) -> List[str]:
        """
        Validates all configured endpoints at startup.
        Returns a list of human-readable diagnostic messages or validation warnings.
        """
        messages = []
        for name, service in self.services.items():
            if not service.enabled:
                messages.append(f"Service '{name}': disabled in configuration.")
                continue

            if not service.is_configured():
                if "REPLACE-WITH" in service.base_url:
                    messages.append(f"Service '{name}': placeholder endpoint detected. Model marked NOT_CONFIGURED until genuine URL is set in model_endpoints.yaml.")
                else:
                    messages.append(f"Service '{name}': unconfigured (base_url is empty).")
                continue

            # Validate URL structure
            try:
                parsed = urlparse(service.base_url)
                if not parsed.scheme or not parsed.netloc:
                    messages.append(f"Service '{name}': invalid URL format '{service.base_url}'. Expected http:// or https:// scheme.")
                else:
                    messages.append(f"Service '{name}': configured at {service.base_url} ({service.api_type}).")
            except Exception as e:
                messages.append(f"Service '{name}': URL parsing error: {str(e)}.")

        return messages

class CentralConfigManager:
    """Singleton holder for authoritative model endpoints configuration."""
    _instance: Optional[EndpointsConfiguration] = None

    @classmethod
    def get_config(cls, reload: bool = False) -> EndpointsConfiguration:
        if cls._instance is None or reload:
            cls._instance = EndpointsConfiguration.load_from_file()
        return cls._instance

    @classmethod
    def reload(cls) -> EndpointsConfiguration:
        cls._instance = EndpointsConfiguration.load_from_file()
        return cls._instance

# Authoritative singleton export
endpoint_config = CentralConfigManager.get_config()

