import json
import os
from typing import List, Tuple, Dict, Any
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

    # --- Metadata Mapping ---
    flor_metadata_mapping: Dict[str, int] = field(
        default_factory=lambda: {"tratamento": 1, "parcela": 2, "ramo": 3, "no": 4}
    )
    fruto_metadata_mapping: Dict[str, int] = field(
        default_factory=lambda: {"tratamento": 1, "bloco": 2, "ramo": 3, "no": 4}
    )

    # --- File Parsing & Classification ---
    exclude_keywords: List[str] = field(
        default_factory=lambda: ["template", "esquemas", "print"]
    )
    date_format: str = "%d%m%y"
    metadata_regex: str = r"(Flor|Fruto)"
    sheet_keywords: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "template": ["template"],
            "flor": ["flor"],
            "fruto": ["fruto"],
        }
    )

    # --- Categorical Columns ---
    flor_categories: List[str] = field(
        default_factory=lambda: ["fazenda", "tratamento", "parcela", "ramo", "no"]
    )
    fruto_categories: List[str] = field(
        default_factory=lambda: ["fazenda", "tratamento", "bloco", "ramo", "no"]
    )

    # --- Agrilyzer / Weather Settings ---
    farms: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: {
            "vicente": {"lat": -15.399654, "lon": -39.237321},
            "felipe": {"lat": -15.299560, "lon": -39.145943},
        }
    )
    weather_params: List[str] = field(
        default_factory=lambda: [
            "T2M",
            "ALLSKY_SFC_SW_DWN",
            "PRECTOTCORR",
            "RH2M",
            "T2M_MAX",
            "T2M_MIN",
        ]
    )
    weather_dual_axis: Dict[str, Any] = field(
        default_factory=lambda: {
            "left": ["PRECTOTCORR"],
            "right": ["T2M", "VPD"],
            "left_label": "Precipitation (mm/day)",
            "right_label": "Temp (°C) / VPD (kPa)",
        }
    )

    @classmethod
    def from_json(cls, path: str):
        """Loads configuration from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)

        proc = data.get("processing", {})
        sheets = data.get("sheets", {})
        flor = sheets.get("flor", {})
        fruto = sheets.get("fruto", {})
        farms = data.get("farms", {})
        weather = data.get("weather", {})

        return cls(
            flor_header_row_index=flor.get("header_row", 2),
            flor_features=flor.get("features", []),
            flor_plant_blocks=[tuple(x) for x in flor.get("plant_blocks", [])],
            flor_metadata_mapping=flor.get("metadata_mapping", {}),
            flor_categories=flor.get("categories", []),
            fruto_header_row_index=fruto.get("header_row", 3),
            fruto_features=fruto.get("features", []),
            fruto_plant_blocks=[tuple(x) for x in fruto.get("plant_blocks", [])],
            fruto_metadata_mapping=fruto.get("metadata_mapping", {}),
            fruto_categories=fruto.get("categories", []),
            exclude_keywords=proc.get("exclude_keywords", []),
            date_format=proc.get("date_format", "%d%m%y"),
            metadata_regex=proc.get("metadata_regex", r"(Flor|Fruto)"),
            sheet_keywords={k: v.get("keywords", []) for k, v in sheets.items()},
            farms=farms,
            weather_params=weather.get("params", []),
            weather_dual_axis=weather.get("dual_axis", {}),
        )


# Global settings instance
settings = ProcessingConfig()


def load_config(path: str = "data/schema.json"):
    """Loads the global settings from a JSON file if it exists."""
    global settings
    if os.path.exists(path):
        settings = ProcessingConfig.from_json(path)
    return settings


# Auto-load if default schema exists
load_config()
