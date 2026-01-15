from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Protocol, List

from pulse_report.domain.pcr import Pcr


class PcrRepository(Protocol):
    def save(self, pcr: Pcr) -> None: ...
    def get(self, pcr_id: str) -> Optional[Pcr]: ...
    def list(self) -> List[Pcr]: ...


@dataclass
class InMemoryPcrRepository(PcrRepository):
    _store: Dict[str, Pcr] = field(default_factory=dict)

    def save(self, pcr: Pcr) -> None:
        self._store[pcr.pcr_id] = pcr

    def get(self, pcr_id: str) -> Optional[Pcr]:
        return self._store.get(pcr_id)

    def list(self) -> List[Pcr]:
        return list(self._store.values())

