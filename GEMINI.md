# Data Filtering and Extraction Guide

This document outlines the business rules and technical specifications for extracting and filtering data from the Harvista Excel workbooks.

## 1. Sheet Classification
Data is categorized based on sheet names (case-insensitive):

| Category | Filter Criteria | Purpose |
| :--- | :--- | :--- |
| **Flor Data** | Contains `flor`, excludes `template` | Reproductive/Flowering stage measurements. |
| **Fruto Data** | Contains `fruto`, excludes `template` | Fruit development stage measurements. |
| **Templates** | Contains `template` | Reference structure for data entry. |
| **Support** | `Esquemas`, `PRINTCampo` | Metadata, treatment definitions, and field layouts. |

## 2. Sheet Structure & Headers
The Excel sheets use a multi-row header structure that requires specific handling during extraction:

*   **Row 1 (Metadata):** Contains labels like `Fazenda:`, `Tratamento`, and grouped headers for `Planta 1`, `Planta 2`, etc.
*   **Row 2 (Primary Headers):** Contains the actual column names (e.g., `S1`, `S2`, `Flor`, `Star`). **This is the row to use as the header.**
*   **Data Rows:** Actual measurements start from **Row 3** onwards.

## 3. Data Cleaning Rules
When processing data into DataFrames or CSVs:

1.  **Column Normalization:**
    *   Convert to lowercase.
    *   Replace spaces with underscores (`_`).
    *   Remove special characters/accents (e.g., `nó` -> `no`).
    *   Strip leading/trailing whitespace.
2.  **Row Filtering:**
    *   Skip the first row of the Excel sheet to reach the primary headers.
    *   Handle `NaN` values in identification columns (`fazenda`, `tratamento`) which are often merged in Excel. Use "forward fill" logic if necessary.

## 4. Key Data Points
*   **Identification:** `fazenda`, `tratamento`, `parcela`, `ramo`, `no`.
*   **Measurements:** `s1` through `s6` (likely developmental stages), `flor`, `star`, `chum` (chumbinho), `fruto`, `rv` (retorno vegetativo).
*   **Replication:** Data is often repeated across columns for `Replica 1` through `Replica 4`.

## 5. CLI Implementation

The `excelxtract` CLI implements these rules via distinct subcommands:

*   **`extract`**: Handles **Sheet Classification** (Rule 1) and **Row Filtering** (Rule 2). It iterates through the workbook, identifies relevant sheets, and exports them to CSV.
*   **`process`**: Implements **Data Cleaning** (Rule 3) and **Key Data Points** extraction (Rule 4). It uses the configuration in `src/excelxtract/config.py` to map columns and plant blocks.
*   **`analyze`**: Generates the visual reports described in the methodology.

To customize the column mappings (e.g., if the Excel layout changes), modify `src/excelxtract/config.py`.
