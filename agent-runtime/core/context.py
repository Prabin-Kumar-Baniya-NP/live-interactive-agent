from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SessionContext:
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    session_template_id: Optional[str] = None
    observations: List[str] = field(default_factory=list)
    session_flags: Dict[str, Any] = field(default_factory=dict)
    modality_state: Dict[str, bool] = field(
        default_factory=lambda: {"camera": False, "screenshare": False}
    )
    panel_state: Dict[str, Any] = field(default_factory=dict)

    def add_observation(self, observation: str) -> None:
        """Add a new observation to the session context."""
        self.observations.append(observation)

    def set_flag(self, key: str, value: Any) -> None:
        """Set a session flag."""
        self.session_flags[key] = value

    def get_flag(self, key: str, default: Any = None) -> Any:
        """Get a session flag."""
        return self.session_flags.get(key, default)
