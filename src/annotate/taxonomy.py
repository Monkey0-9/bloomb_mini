"""
Class Taxonomy — Phase 3.2

Define per use-case, never reuse across use-cases.
Each taxonomy is frozen after annotation begins to prevent
label contamination.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class UseCase(str, Enum):
    PORT_THROUGHPUT = "port_throughput"
    RETAIL_FOOTFALL = "retail_footfall"
    INDUSTRIAL_OUTPUT = "industrial_output"


@dataclass(frozen=True)
class ClassDefinition:
    """Single class in a taxonomy."""
    class_id: int
    class_name: str
    description: str
    color_rgb: tuple[int, int, int]  # For visualization
    min_area_px: int = 10  # Minimum annotation area
    parent_class: str | None = None  # For hierarchical taxonomies


@dataclass
class Taxonomy:
    """Complete class taxonomy for a use-case."""
    use_case: UseCase
    version: str
    classes: list[ClassDefinition]
    frozen: bool = False
    notes: str = ""

    def get_class_names(self) -> list[str]:
        return [c.class_name for c in self.classes]

    def get_class_by_name(self, name: str) -> ClassDefinition | None:
        return next((c for c in self.classes if c.class_name == name), None)

    def get_num_classes(self) -> int:
        return len(self.classes)

    def freeze(self) -> None:
        """Freeze taxonomy — no modifications allowed after annotation begins."""
        self.frozen = True

    def to_coco_categories(self) -> list[dict[str, Any]]:
        """Export as COCO format category list."""
        return [
            {
                "id": c.class_id,
                "name": c.class_name,
                "supercategory": c.parent_class or "none",
            }
            for c in self.classes
        ]


# ═══════════════════════════════════════════════════════════════════
# Use-Case Taxonomies (per spec Phase 3.2)
# ═══════════════════════════════════════════════════════════════════

PORT_THROUGHPUT_TAXONOMY = Taxonomy(
    use_case=UseCase.PORT_THROUGHPUT,
    version="1.0.0",
    classes=[
        ClassDefinition(1, "container_stack", "Stacked shipping containers on dock", (255, 100, 0), min_area_px=25),
        ClassDefinition(2, "vessel_at_berth", "Ship docked at a berth/pier", (0, 100, 255), min_area_px=100),
        ClassDefinition(3, "empty_berth", "Berth/pier without any docked vessel", (200, 200, 200), min_area_px=50),
        ClassDefinition(4, "crane_active", "Gantry crane engaged in loading/unloading", (255, 255, 0), min_area_px=20),
        ClassDefinition(5, "truck_queue", "Queue of trucks waiting at port gate/yard", (150, 50, 50), min_area_px=30),
        ClassDefinition(6, "vessel_anchored", "Ship at anchor outside berth area", (0, 50, 200), min_area_px=80),
        ClassDefinition(7, "yard_equipment", "RTG/straddle carrier/forklift in container yard", (100, 200, 100), min_area_px=15),
    ],
    notes="Phase 1 primary taxonomy for Asia-Pacific port monitoring",
)

RETAIL_FOOTFALL_TAXONOMY = Taxonomy(
    use_case=UseCase.RETAIL_FOOTFALL,
    version="1.0.0",
    classes=[
        ClassDefinition(1, "car", "Passenger vehicle in parking lot", (0, 150, 255), min_area_px=8),
        ClassDefinition(2, "empty_space", "Empty parking space", (200, 200, 200), min_area_px=8),
        ClassDefinition(3, "loading_dock", "Commercial loading/unloading bay", (255, 150, 0), min_area_px=30),
        ClassDefinition(4, "pedestrian_zone", "Walkway/sidewalk area with foot traffic", (0, 255, 150), min_area_px=20),
        ClassDefinition(5, "truck", "Commercial truck/delivery vehicle", (150, 0, 200), min_area_px=15),
    ],
    notes="Phase 2 taxonomy for retail parking lot occupancy",
)

INDUSTRIAL_OUTPUT_TAXONOMY = Taxonomy(
    use_case=UseCase.INDUSTRIAL_OUTPUT,
    version="1.0.0",
    classes=[
        ClassDefinition(1, "thermal_plume_active", "Heat plume from active smokestack/vent (visible in thermal)", (255, 0, 0), min_area_px=20),
        ClassDefinition(2, "thermal_plume_inactive", "Smokestack/vent with no visible thermal plume", (100, 100, 100), min_area_px=20),
        ClassDefinition(3, "smokestack", "Industrial chimney/exhaust structure", (200, 100, 0), min_area_px=10),
        ClassDefinition(4, "cooling_tower", "Cooling tower (natural or forced draft)", (0, 200, 200), min_area_px=30),
        ClassDefinition(5, "storage_tank", "Cylindrical storage tank (oil, gas, chemical)", (150, 150, 0), min_area_px=15),
        ClassDefinition(6, "conveyor_belt", "Material transport conveyor system", (100, 100, 200), min_area_px=10),
    ],
    notes="Phase 2 taxonomy for industrial facility thermal monitoring",
)

# Master registry
TAXONOMIES = {
    UseCase.PORT_THROUGHPUT: PORT_THROUGHPUT_TAXONOMY,
    UseCase.RETAIL_FOOTFALL: RETAIL_FOOTFALL_TAXONOMY,
    UseCase.INDUSTRIAL_OUTPUT: INDUSTRIAL_OUTPUT_TAXONOMY,
}


def get_taxonomy(use_case: UseCase) -> Taxonomy:
    """Get the taxonomy for a specific use-case."""
    tax = TAXONOMIES.get(use_case)
    if not tax:
        raise ValueError(f"No taxonomy defined for use-case: {use_case}")
    return tax
