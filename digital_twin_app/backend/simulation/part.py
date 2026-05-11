"""Part dataclass representing a workpiece flowing through the assembly line."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Part:
    """Represents a single part flowing through the assembly line.

    Tracks timestamps at each station for lead time and waiting time analysis.
    """

    part_id: int
    creation_time: float
    entry_times: Dict[str, float] = field(default_factory=dict)
    start_times: Dict[str, float] = field(default_factory=dict)
    exit_times: Dict[str, float] = field(default_factory=dict)
    completion_time: Optional[float] = None

    def record_entry(self, station_name: str, time: float) -> None:
        self.entry_times[station_name] = time

    def record_start(self, station_name: str, time: float) -> None:
        self.start_times[station_name] = time

    def record_exit(self, station_name: str, time: float) -> None:
        self.exit_times[station_name] = time

    def waiting_time_at(self, station_name: str) -> float:
        entry = self.entry_times.get(station_name)
        start = self.start_times.get(station_name)
        if entry is not None and start is not None:
            return max(0.0, start - entry)
        return 0.0

    @property
    def lead_time(self) -> Optional[float]:
        if self.completion_time is not None:
            return self.completion_time - self.creation_time
        return None
