import logging
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel


class FeatureDefinition(BaseModel):
    name: str
    description: str
    category: str
    window_seconds: int
    parameters: Optional[Dict] = {}


class FeatureRegistry:
    """
    Central Registry for all available features.
    Loads definitions from YAML to ensure consistency.
    """

    def __init__(self, config_path: str = "backend/feature_store/features.yaml"):
        self.features: Dict[str, FeatureDefinition] = {}
        self._load_config(config_path)
        self.logger = logging.getLogger(__name__)

    def _load_config(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            for item in data.get("features", []):
                feature = FeatureDefinition(**item)
                self.features[feature.name] = feature

        except Exception as e:
            raise RuntimeError(f"Failed to load feature registry from {path}: {e}")

    def get_feature(self, name: str) -> Optional[FeatureDefinition]:
        return self.features.get(name)

    def list_features(self) -> List[FeatureDefinition]:
        return list(self.features.values())
