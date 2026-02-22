# excelxtract: Phenological Data Pipeline

`excelxtract` is a modular Python package designed for the automated extraction, normalization, and unsupervised analysis of agricultural developmental stage (phenology) data. It converts complex, multi-sheet Excel field logs into machine-learning-ready (ML-ready) tidy datasets and provides insightful visual analytics.

## 🚀 Key Features

- **Automated ETL Pipeline**: Ingests multi-sheet `.xlsx` files and converts them into standardized CSVs.
- **Intelligent Processing**: Automatically transforms "Wide" Excel layouts into "Tidy/Long" formats, handling forward-fills and cross-sheet classifications.
- **Time-Series Ready IDs**: Generates persistent sample IDs (`f{farm}_p{plant}_{trat}_parc{val}_r{branch}_n{node}`) to track specific biological units over time, independent of observation dates.
- **Unsupervised Learning Dashboard**: Performs Dimensionality Reduction (PCA) and Manifold Learning (t-SNE) to identify phenological clusters and treatment effects.
- **Visual Profiling**: Generates stacked bar charts of developmental stages by date and treatment.
- **Compartmentalized Architecture**: Clean separation between ingestion, processing, analysis, and utilities.

## 📂 Project Structure

```text
.
├── data/               # Raw Excel workbooks (.xlsx)
├── output/             # Generated outputs
│   ├── csv/            # Raw intermediate CSV sheets
│   ├── ml_ready/       # Unified, tidy CSV tables (Final datasets)
│   └── analysis/       # Generated plots and cluster dashboards
├── src/excelxtract/    # Core package source code
│   ├── loader.py       # Excel ingestion and sheet classification
│   ├── processor.py    # Wide-to-Long transformation logic
│   ├── analysis.py     # PCA, t-SNE, and plotting suite
│   └── utils.py        # Normalization and safe type casting
├── reports/            # Technical methodology and reports
└── main.py             # Pipeline orchestration script
```

## 🛠️ Installation

This project uses `uv` for lightning-fast dependency management.

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd excelxtract
   ```

2. **Sync dependencies**:
   ```bash
   uv sync
   ```

## 📈 Usage

To run the complete end-to-end pipeline (ETL + Analysis):

```bash
uv run python main.py
```

### Pipeline Steps:
1. **Extraction**: Converts `data/*.xlsx` sheets into raw CSVs in `output/csv/`.
2. **Normalization**: Merges sheets into "Flor" and "Fruto" master tables in `output/ml_ready/`.
3. **Analysis**: Performs PCA/t-SNE clustering and generates visual reports in `output/analysis/`.

## 🔬 Methodology

The system uses a **Synthetic Primary Key** for identity tracking:
`f{fazenda}_p{planta}_{tratamento}_parc{val}_r{ramo}_n{no}`

By excluding the date from the ID, the pipeline allows for longitudinal analysis of the same plant across different developmental windows. For a deep dive into the engineering choices and mathematical approaches, see [reports/methodology.md](reports/methodology.md).

## 📊 Analytics Dashboard

The pipeline automatically generates several key visualizations:
- **`flor_stages_by_date.png`**: Stacked progression of flowering stages over time.
- **`clustering_clustering.png`**: Side-by-side dashboard of PCA (variance-based) and t-SNE (local structure) clustering of plant conditions.

## 📝 License

Internal Project / AidBio.
**Author**: Cleverson Matiolli, PhD.
**Engineering**: Senior Peer Developer / Gemini CLI.
