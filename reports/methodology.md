# Technical Report: `excelxtract` Pipeline
**Subject:** Engineering Modular ETL and Unsupervised Analysis for Agricultural Phenology Data  
**Author:** Gemini CLI (Data Science & Engineering)  
**Date:** February 21, 2026

---

### 1. Executive Summary
The `excelxtract` package is a specialized Python framework designed to bridge the gap between unstructured field-collected Excel data and machine-learning-ready (ML-ready) datasets. It automates the extraction, normalization, and unsupervised analysis of developmental stages (phenology) for flowers and fruits.

### 2. System Architecture
The package follows a **decoupled, modular architecture** to ensure maintainability and scalability. The logic is divided into four functional layers:

*   **`loader.py` (Ingestion Layer):** Handles the raw conversion of multi-sheet `.xlsx` workbooks into standardized CSV intermediates. It includes classification logic to differentiate between "Flor", "Fruto", and "Template" sheets.
*   **`processor.py` (Domain Logic Layer):** Contains the core heuristic rules for parsing the unique spatial layout of the field sheets. It transforms "Wide" Excel formats (where multiple plants are listed side-by-side) into "Long/Tidy" formats.
*   **`analysis.py` (Insight Layer):** Implements a Data Science suite using `scikit-learn`, `seaborn`, and `matplotlib` to perform automated visual and statistical profiling.
*   **`utils.py` (Foundation Layer):** Provides idempotent functions for string normalization, safe type casting, and regex-based metadata extraction.

### 3. Data Engineering & Transformation
#### A. Naming Conventions & Identity Tracking
A critical requirement for time-series analysis is the ability to track a specific biological unit across multiple observation dates. We implemented a **Synthetic Primary Key** (the `sample_name`) that excludes the date to maintain identity:

**Schema:** `f{fazenda}_p{planta}_{tratamento}_parc{val}_r{ramo}_n{no}`

*   **`f` (Fazenda):** Normalized farm name.
*   **`p` (Planta):** Plant ID (1, 2, or 3).
*   **`t` (Tratamento):** Case-insensitive treatment code (e.g., `t1`, `t2`).
*   **`parc` (Parcela/Bloco):** Normalized spatial unit. In "Fruto" sheets, `bloco` is mapped to `parc` to ensure parity with "Flor" records.
*   **`r` (Ramo):** Simplified branch direction (`dir` or `esq`).

#### B. ETL Logic (Extraction, Transformation, Load)
*   **Wide-to-Long Transformation:** The logic identifies "plant blocks" (specific column ranges) and iterates through them to create a single row per observation.
*   **Forward-Filling (FFill):** Field sheets often use merged cells for farm and treatment names. The pipeline programmatically "fills down" these values to ensure every data row is self-describing.
*   **Robust Casting:** We implemented a `to_int` utility that handles floating-point strings (e.g., `"1.0"`) and `NaN` values, converting them to clean integers to prevent schema breaks in downstream ML models.

### 4. Unsupervised Learning & Analytics
The pipeline concludes with an automated analysis phase to identify patterns in developmental stages without prior labeling:

1.  **Dimensionality Reduction (PCA):** Principal Component Analysis is used to project the 9-11 developmental features into a 2D plane. This reveals the "variance-driving" stages and indicates if treatments are fundamentally changing the phenological signature.
2.  **Manifold Learning (t-SNE):** t-Distributed Stochastic Neighbor Embedding provides a non-linear look at the data, grouping similar plant states. This is particularly effective for identifying outliers or "stalled" developmental paths.
3.  **Temporal Stacked Profiling:** The system generates stacked bar charts that visualize the evolution of stage counts over time, allowing researchers to see the "shift" from early stages (`s1-s6`) to fruit set.

### 5. Output Inventory
The pipeline produces a structured `output/` directory:

*   **`output/csv/`**: Cleaned, individual sheet backups for audit trails.
*   **`output/ml_ready/`**: 
    *   `final_flor_data.csv`: Unified time-series for flowering stages.
    *   `final_fruto_data.csv`: Unified time-series for fruiting/harvest stages.
*   **`output/analysis/`**: 
    *   `clustering_clustering.png`: Side-by-side PCA and t-SNE dashboards.
    *   `stages_by_date.png`: Visual progression of developmental counts.
    *   `stages_by_trat.png`: Comparative analysis of treatment efficacy.

### 6. Conclusion
The `excelxtract` package effectively converts manual field observations into a high-integrity data asset. By abstracting the complex Excel structure into a compartmentalized Python package, we have created a repeatable, verifiable path for longitudinal phenological research.
