"""Part dataclass representing a workpiece flowing through the assembly line."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Part:
    """Represents a single part flowing through the assembly line.

    Tracks timestamps at each station for lead time and waiting time analysis.

    Attributes:
        part_id: Unique identifier for this part
        creation_time: Simulation time when the part was created
        entry_times: Dict mapping station name to time part entered the buffer
        start_times: Dict mapping station name to time processing started
        exit_times: Dict mapping station name to time processing completed
        completion_time: Simulation time when the part exited the last station
    """
    part_id: int
    creation_time: float
    entry_times: Dict[str, float] = field(default_factory=dict)
    start_times: Dict[str, float] = field(default_factory=dict)
    exit_times: Dict[str, float] = field(default_factory=dict)
    completion_time: Optional[float] = None

    def record_entry(self, station_name: str, time: float) -> None:
        """Record when the part entered a station's buffer.

        Args:
            station_name: Name of the station
            time: Current simulation time
        """
        self.entry_times[station_name] = time

    def record_start(self, station_name: str, time: float) -> None:
        """Record when processing started at a station.

        Args:
            station_name: Name of the station
            time: Current simulation time
        """
        self.start_times[station_name] = time

    def record_exit(self, station_name: str, time: float) -> None:
        """Record when the part exited a station after processing.

        Args:
            station_name: Name of the station
            time: Current simulation time
        """
        self.exit_times[station_name] = time

    def waiting_time_at(self, station_name: str) -> float:
        """Calculate waiting time in buffer at a given station.

        Args:
            station_name: Name of the station

        Returns:
            Waiting time in seconds, or 0.0 if timestamps are missing
        """
        entry = self.entry_times.get(station_name)
        start = self.start_times.get(station_name)
        if entry is not None and start is not None:
            return max(0.0, start - entry)
        return 0.0

    def processing_time_at(self, station_name: str) -> float:
        """Calculate actual processing time at a given station.

        Args:
            station_name: Name of the station

        Returns:
            Processing time in seconds, or 0.0 if timestamps are missing
        """
        start = self.start_times.get(station_name)
        exit_t = self.exit_times.get(station_name)
        if start is not None and exit_t is not None:
            return max(0.0, exit_t - start)
        return 0.0

    @property
    def lead_time(self) -> Optional[float]:
        """Total lead time from creation to completion.

        Returns:
            Lead time in seconds, or None if part is not yet complete
        """
        if self.completion_time is not None:
            return self.completion_time - self.creation_time
        return None
