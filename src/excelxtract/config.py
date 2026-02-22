from typing import List, Tuple
from dataclasses import dataclass, field


@dataclass
class ProcessingConfig:
    """Configuration for parsing Excel/CSV structures."""

    # --- Flor (Flower) Sheet Settings ---
    # Number of header rows to skip before data starts
    flor_header_row_index: int = 2

    # Column names for features
    flor_features: List[str] = field(
        default_factory=lambda: [
            "s1",
            "s2",
            "s3",
            "s4",
            "s5",
            "s6",
            "flor",
            "star",
            "chumb",
            "fruto",
            "rv",
        ]
    )

    # Plant Blocks: List of (Plant ID, Start Column Index)
    flor_plant_blocks: List[Tuple[int, int]] = field(
        default_factory=lambda: [(1, 5), (2, 17), (3, 29)]
    )

    # --- Fruto (Fruit) Sheet Settings ---
    fruto_header_row_index: int = 3
    fruto_features: List[str] = field(
        default_factory=lambda: [
            "s1_flor_gemas",
            "s1_flor_star",
            "s1_flor_chumb",
            "fruto_verde",
            "fruto_parcial",
            "fruto_vermelho",
            "fruto_passa",
            "fruto_secos",
            "rv",
        ]
    )
    fruto_plant_blocks: List[Tuple[int, int]] = field(
        default_factory=lambda: [(1, 5), (2, 15), (3, 25)]
    )


# Global settings instance
settings = ProcessingConfig()
