"""
Base Rule Interface for KiSignal-Guard.
Follows the Strategy / Visitor design pattern for extensible semantic verification.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from kisignal_guard.core.models import BoardSnapshot, Violation, RuleCategory


class BaseRule(ABC):
    """Abstract Base Class for all electrical/semantic verification rules."""

    def __init__(self, rule_id: str, name: str, category: RuleCategory, enabled: bool = True):
        self.rule_id = rule_id
        self.name = name
        self.category = category
        self.enabled = enabled
        self.config: Dict[str, Any] = {}

    def configure(self, config: Dict[str, Any]) -> None:
        """Update rule threshold parameters dynamically."""
        self.config.update(config)

    @abstractmethod
    def check(self, board: BoardSnapshot) -> List[Violation]:
        """
        Executes analysis against the provided BoardSnapshot.
        Returns a list of Violation objects found on the board.
        """
        pass
