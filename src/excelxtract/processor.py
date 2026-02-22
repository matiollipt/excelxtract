import pandas as pd
import os
import re
from .utils import normalize_ramo, to_int, extract_meta_from_filename, track_iterator
from typing import Tuple, List, Dict, Any
from .config import settings, ProcessingConfig


def process_flor_df(
    file_path: str, fazenda: str, date: str, config: ProcessingConfig = settings
) -> pd.DataFrame:
    """Processes a 'Flor' (Flower) CSV file into a tidy DataFrame.

    Args:
        file_path: Path to the CSV file.
        fazenda: Name of the farm (extracted from filename).
        date: Date of the record (extracted from filename).
        config: Configuration object containing layout settings.

    Returns:
        A pandas DataFrame containing the tidy data with columns for
        sample metadata and feature counts.
    """
    df = pd.read_csv(file_path, header=None)
    data = df.iloc[config.flor_header_row_index :].copy()

    # Forward fill metadata
    data[1] = data[1].ffill()  # Tratamento
    data[2] = data[2].ffill()  # Parcela
    data[3] = data[3].ffill()  # Ramo

    features = config.flor_features
    all_rows = []

    plant_blocks = config.flor_plant_blocks
    block_width = len(features)

    for _, row in data.iterrows():
        if pd.isna(row[4]):
            continue  # Skip if No is empty

        treatment = str(row[1]).strip().lower()
        parcela = str(row[2]).strip()
        ramo = normalize_ramo(row[3])
        no = str(row[4]).strip()

        for plant_id, start_col in plant_blocks:
            sample_name = (
                f"f{fazenda}_p{plant_id}_{treatment}_parc{parcela}_r{ramo}_n{no}"
            )

            row_values = row.iloc[start_col : start_col + block_width].values
            if pd.isna(row_values).all():
                continue

            row_dict = {
                "sample_name": sample_name,
                "fazenda": fazenda,
                "date": date,
                "planta": plant_id,
                "tratamento": treatment,
                "parcela": parcela,
                "ramo": ramo,
                "no": no,
            }
            for i, feat in enumerate(features):
                row_dict[feat] = to_int(row_values[i])

            all_rows.append(row_dict)

    df_out = pd.DataFrame(all_rows)
    if df_out.empty:
        return df_out

    # Enforce data types for efficient storage and analysis
    df_out["date"] = pd.to_datetime(df_out["date"])

    cat_cols = ["fazenda", "tratamento", "parcela", "ramo", "no"]
    for col in cat_cols:
        if col in df_out.columns:
            df_out[col] = df_out[col].astype("category")

    return df_out


def process_fruto_df(
    file_path: str, fazenda: str, date: str, config: ProcessingConfig = settings
) -> pd.DataFrame:
    """Processes a 'Fruto' (Fruit) CSV file into a tidy DataFrame.

    Args:
        file_path: Path to the CSV file.
        fazenda: Name of the farm.
        date: Date of the record.
        config: Configuration object containing layout settings.

    Returns:
        A pandas DataFrame containing the tidy data.
    """
    df = pd.read_csv(file_path, header=None)
    data = df.iloc[config.fruto_header_row_index :].copy()

    data[1] = data[1].ffill()  # Tratamento
    data[2] = data[2].ffill()  # Bloco
    data[3] = data[3].ffill()  # Ramo

    features = config.fruto_features

    all_rows = []
    plant_blocks = config.fruto_plant_blocks
    block_width = len(features)

    for _, row in data.iterrows():
        if pd.isna(row[4]):
            continue

        treatment = str(row[1]).strip().lower()
        bloco = str(row[2]).strip()
        ramo = normalize_ramo(row[3])
        no = str(row[4]).strip()

        for plant_id, start_col in plant_blocks:
            # We map bloco to 'parc' to keep consistency with Flor sheets for time-series.
            sample_name = (
                f"f{fazenda}_p{plant_id}_{treatment}_parc{bloco}_r{ramo}_n{no}"
            )

            row_values = row.iloc[start_col : start_col + block_width].values
            if pd.isna(row_values).all():
                continue

            row_dict = {
                "sample_name": sample_name,
                "fazenda": fazenda,
                "date": date,
                "planta": plant_id,
                "tratamento": treatment,
                "bloco": bloco,
                "ramo": ramo,
                "no": no,
            }
            for i, feat in enumerate(features):
                row_dict[feat] = to_int(row_values[i])

            all_rows.append(row_dict)

    df_out = pd.DataFrame(all_rows)
    if df_out.empty:
        return df_out

    # Enforce data types
    df_out["date"] = pd.to_datetime(df_out["date"])

    cat_cols = ["fazenda", "tratamento", "bloco", "ramo", "no"]
    for col in cat_cols:
        if col in df_out.columns:
            df_out[col] = df_out[col].astype("category")

    return df_out


def process_all_csvs(
    output_dir: str = "output/csv", config: ProcessingConfig = settings
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Orchestrates the processing of all CSV files in a directory.

    Iterates through the output directory, identifies Flor and Fruto files,
    processes them, and aggregates them into two main DataFrames.

    Args:
        output_dir: Directory containing the raw CSV files.
        config: Configuration object to pass to processors.

    Returns:
        A tuple containing two DataFrames: (final_flor_df, final_fruto_df).
    """
    flor_dfs = []
    fruto_dfs = []

    # Filter files first to allow progress bar to know total count
    all_files = [f for f in os.listdir(output_dir) if f.endswith(".csv")]

    for filename in track_iterator(all_files, description="Processing CSV files"):
        # Skip non-data files
        lower_name = filename.lower()
        if any(x in lower_name for x in ["template", "esquemas", "print"]):
            continue

        file_path = os.path.join(output_dir, filename)
        fazenda, date = extract_meta_from_filename(filename)

        if "flor" in filename.lower():
            df = process_flor_df(file_path, fazenda, date, config=config)
            flor_dfs.append(df)
        elif "fruto" in filename.lower():
            df = process_fruto_df(file_path, fazenda, date, config=config)
            fruto_dfs.append(df)

    final_flor = pd.concat(flor_dfs, ignore_index=True) if flor_dfs else pd.DataFrame()
    final_fruto = (
        pd.concat(fruto_dfs, ignore_index=True) if fruto_dfs else pd.DataFrame()
    )

    return final_flor, final_fruto
