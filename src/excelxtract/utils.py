import re
import unicodedata
import os
from datetime import datetime
from typing import Any, Tuple, Optional, Union
from typing import Iterable
from rich.console import Console
from rich.progress import track

# Global console instance for consistent styling
console = Console()


def track_iterator(sequence: Iterable, description: str = "Processing...") -> Iterable:
    """Wraps an iterable with a visual progress bar.

    Args:
        sequence: The iterable to loop over.
        description: Text to display next to the progress bar.

    Returns:
        An iterable that yields values from the original sequence while updating the UI.
    """
    return track(sequence, description=description)


def log_info(message: str) -> None:
    """Logs an informational message."""
    console.print(f"[bold blue]INFO[/bold blue]: {message}")


def log_success(message: str) -> None:
    """Logs a success message."""
    console.print(f"[bold green]SUCCESS[/bold green]: {message}")


def log_warning(message: str) -> None:
    """Logs a warning message."""
    console.print(f"[bold yellow]WARNING[/bold yellow]: {message}")


def log_error(message: str) -> None:
    """Logs an error message."""
    console.print(f"[bold red]ERROR[/bold red]: {message}")


def normalize_name(name: str) -> str:
    """Normalizes a string for use as a column name or filename.

    Removes accents, special characters, and replaces spaces with underscores.

    Args:
        name: The input string to normalize.

    Returns:
        A normalized, lowercase string safe for filenames or identifiers.
    """
    if not name:
        return ""
    name = "".join(
        c
        for c in unicodedata.normalize("NFD", str(name))
        if unicodedata.category(c) != "Mn"
    )
    name = name.strip().lower().replace(" ", "_")
    name = re.sub(r"[^a-z0-9_]", "", name)
    return name


def normalize_ramo(val: Any) -> Union[str, float, None]:
    """Formats the 'Ramo' (Branch) string.

    Removes dots and whitespace. Example: "Dir." -> "Dir".

    Args:
        val: The raw value from the dataframe (string, float, or None).

    Returns:
        The cleaned string, or the original value if it is NaN/None.
    """
    if val is None or (isinstance(val, float) and (val != val)):  # check for NaN
        return val
    return str(val).replace(".", "").strip()


def extract_meta_from_filename(filename: str) -> Tuple[str, str]:
    """Extracts farm name (fazenda) and date from a standardized filename.

    Expected format involves parts separated by underscores, containing a
    6-digit date (ddmmyy).

    Args:
        filename: The filename to parse.

    Returns:
        A tuple containing (fazenda_name, date_string_yyyy_mm_dd).
    """
    base = os.path.splitext(filename)[0]
    parts = base.split("_")

    date_str = ""
    fazenda = ""

    for p in parts:
        if p.isdigit() and len(p) == 6:
            date_str = p
        else:
            res = re.sub(r"(Flor|Fruto)", "", p, flags=re.IGNORECASE)
            fazenda = res.strip().lower()

    try:
        date_val = datetime.strptime(date_str, "%d%m%y").strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        date_val = date_str

    return fazenda, date_val


def to_int(val: Any) -> int:
    """Safely converts numeric strings or floats to integers.

    Args:
        val: The input value (str, float, int, or None).

    Returns:
        The integer representation of the value, or 0 if conversion fails
        or value is NaN.
    """
    try:
        if val is None or (isinstance(val, float) and (val != val)):
            return 0
        return int(float(val))
    except (ValueError, TypeError):
        return 0
