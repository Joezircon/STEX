from dataclasses import dataclass, field
from typing import Literal, Optional

ProblemType = Literal[
    "white_island",
    "weak_span",
    "tiny_detail",
    "export_warning",
]

Severity = Literal[
    "info",
    "warning",
    "critical",
]


@dataclass
class ForgeProblem:
    """
    A single manufacturability issue detected by Forge.

    Example:
        white island at x/y position with area and bounding box.
    """

    problem_type: ProblemType
    severity: Severity
    label: str
    message: str
    bbox: tuple[int, int, int, int] | None = None
    centroid: tuple[int, int] | None = None
    area_px: int | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ForgeReport:
    """
    Result returned by Forge after inspection.
    """

    image_width: int
    image_height: int
    problems: list[ForgeProblem] = field(default_factory=list)

    @property
    def white_island_count(self) -> int:
        return sum(1 for p in self.problems if p.problem_type == "white_island")

    @property
    def critical_count(self) -> int:
        return sum(1 for p in self.problems if p.severity == "critical")

    @property
    def is_cut_ready(self) -> bool:
        return self.critical_count == 0

    def summary(self) -> str:
        if self.is_cut_ready:
            return "CUT READY: zero critical issues."
        return f"NOT CUT READY: {self.critical_count} critical issue(s), {self.white_island_count} white island(s)."
