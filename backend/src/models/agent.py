from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentType(str, Enum):
    AIP = "AIP"   # Interfaz con el Paciente
    ASD = "ASD"   # Síntesis de Datos
    AIPER = "AIPer"  # Intervención Personalizada
    AIC = "AIC"   # Informes para el Clínico


@dataclass
class Agent:
    """Minimal agent representation for orchestration and testing."""

    type: AgentType
    state: dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        self.state[key] = value

    def get(self, key: str, default: Any | None = None) -> Any | None:
        return self.state.get(key, default)
