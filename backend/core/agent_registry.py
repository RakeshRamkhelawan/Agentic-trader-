import logging
from typing import Any, Callable, Dict, List

import yaml
from pydantic import BaseModel, ValidationError


class GunaComposition(BaseModel):
    sattva: float
    rajas: float
    tamas: float


class AgentProfile(BaseModel):
    id: str
    name: str
    element: str
    guna_composition: GunaComposition
    system_directive: str  # Nu een 'directive' in plaats van 'prompt'
    allowed_tools: List[str]
    subscriptions: List[str]


class ToolRegistry:
    """
    Central repository of executable tools.
    Maps string names (from YAML) to Python functions.
    """

    _tools: Dict[str, Callable] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register a function as a tool."""

        def decorator(func):
            cls._tools[name] = func
            return func

        return decorator

    @classmethod
    def get_tool(cls, name: str) -> Callable:
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> List[str]:
        return list(cls._tools.keys())


class AgentRegistry:
    """
    Loads agent profiles from YAML.
    """

    def __init__(self, config_path: str = "backend/config/agent_profiles.yaml"):
        self.profiles: Dict[str, AgentProfile] = {}
        self._load_config(config_path)

    def _load_config(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            for item in data.get("agents", []):
                profile = AgentProfile(**item)
                self.profiles[profile.id] = profile

        except ValidationError as e:
            logging.error(
                f"Validation error in agent profile for {item.get('id', 'unknown')}: {e}"
            )
            raise
        except Exception as e:
            logging.error(f"Failed to load agent profiles from {path}: {e}")
            raise

    def get_profile(self, agent_id: str) -> AgentProfile:
        return self.profiles.get(agent_id)
