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
*   **`analyze`**: Generates professional visual reports and performs unsupervised learning. It aggregates data across individual fazendas and produces a global comparative profile.

To customize the column mappings (e.g., if the Excel layout changes), modify `src/excelxtract/config.py`.

## 6. Advanced Analysis & Professional Reporting

The analysis pipeline (`analyze` subcommand) is designed for professional-grade data science insights:

### A. Professional Visualization Suite
*   **Styled Theming:** Uses `seaborn` with `whitegrid` theme and `viridis` colormap for publication-quality output.
*   **Faceted Evolution Plots:** Visualizes developmental stages across multiple dimensions (e.g., `date` vs `fazenda`) using `FacetGrid`.
*   **Complete Phenological Profiles:** Generates aggregated totals for the entire observation period, providing a clear "fingerprint" for each treatment.

### B. Unsupervised Learning Pipeline
*   **PCA Grid Search:** Automatically iterates through different feature subsets (Full Set, Core Stages, High-Variance features) to identify key descriptors.
*   **t-SNE Parameter Sweeps:** Executes a grid of perplexity values (e.g., 5, 15, 30, 50) to ensure stable and reliable cluster identification.

### C. Global Comparative Analysis
*   Aggregates data across all processed fazendas to provide a comparative overview.
*   Outputs individual reports per fazenda and a combined `global_profile` report.
