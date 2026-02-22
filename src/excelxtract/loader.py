import openpyxl
import csv
import os
import pandas as pd
from .utils import normalize_name, track_iterator, log_info
from typing import List, Dict, Tuple


def classify_sheets(sheet_names: List[str]) -> Dict[str, List[str]]:
    """Classifies Excel sheet names into categories based on keywords.

    Args:
        sheet_names: A list of sheet names from the workbook.

    Returns:
        A dictionary with keys 'flor', 'fruto', 'template', 'other',
        containing lists of matching sheet names.
    """
    classification = {"flor": [], "fruto": [], "template": [], "other": []}
    for name in sheet_names:
        sheet_name_lower = name.lower()
        if "template" in sheet_name_lower:
            classification["template"].append(name)
        elif "flor" in sheet_name_lower:
            classification["flor"].append(name)
        elif "fruto" in sheet_name_lower:
            classification["fruto"].append(name)
        else:
            classification["other"].append(name)
    return classification


def excel_to_csv_sheets(
    excel_path: str, output_dir: str = "output/csv", skip_rows: int = 0
) -> List[Tuple[str, str]]:
    """Converts each sheet of an Excel file to a separate CSV file.

    Args:
        excel_path: Path to the source Excel file.
        output_dir: Directory where CSV files will be saved.
        skip_rows: Number of rows to skip at the beginning of each sheet.

    Returns:
        A list of tuples, where each tuple is (original_sheet_name, csv_file_path).

    Raises:
        FileNotFoundError: If the excel_path does not exist.
    """
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    os.makedirs(output_dir, exist_ok=True)
    wb = openpyxl.load_workbook(excel_path, data_only=True)

    sheet_names = wb.sheetnames
    processed_files = []

    log_info(f"Found {len(sheet_names)} sheets in workbook.")

    for name in track_iterator(sheet_names, description="Converting sheets to CSV"):
        sheet = wb[name]
        safe_name = normalize_name(name)
        csv_filename = f"{safe_name}.csv"
        csv_path = os.path.join(output_dir, csv_filename)

        with open(csv_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            rows = list(sheet.values)
            if skip_rows > 0:
                rows = rows[skip_rows:]
            for row in rows:
                writer.writerow(row)

        processed_files.append((name, csv_path))

    return processed_files
