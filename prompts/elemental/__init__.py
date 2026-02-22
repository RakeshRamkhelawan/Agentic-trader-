"""
Elemental Agent Prompts
Vedic-aligned LLM prompts for the 5 elemental agents
"""

import os

PROMPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_prompt(agent_name: str) -> str:
    """Load system prompt for an elemental agent"""
    filepath = os.path.join(PROMPT_DIR, f"{agent_name}_system.txt")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

# Convenience functions
def fire_prompt() -> str:
    """Load Fire Agent (Risk Guardian) prompt"""
    return load_prompt("fire_agent")

def water_prompt() -> str:
    """Load Water Agent (Macro Research) prompt"""
    return load_prompt("water_agent")

def air_prompt() -> str:
    """Load Air Agent (Technical Signals) prompt"""
    return load_prompt("air_agent")

def earth_prompt() -> str:
    """Load Earth Agent (Valuation) prompt"""
    return load_prompt("earth_agent")

def ether_prompt() -> str:
    """Load Ether Agent (Orchestrator) prompt"""
    return load_prompt("ether_agent")

__all__ = [
    "load_prompt",
    "fire_prompt",
    "water_prompt", 
    "air_prompt",
    "earth_prompt",
    "ether_prompt"
]
