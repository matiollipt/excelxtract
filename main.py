import typer
import os
import shutil
import pandas as pd
from src.excelxtract import excel_to_csv_sheets, process_all_csvs, generate_report

app = typer.Typer(help="ExcelXtract CLI: Phenological Data Pipeline")


@app.command()
def extract(
    excel_path: str = typer.Argument(..., help="Path to the input Excel file"),
    output_dir: str = typer.Option(
        "output/csv", "--output-dir", "-o", help="Directory to save raw CSVs"
    ),
    skip_rows: int = typer.Option(0, help="Rows to skip in Excel sheets"),
):
    """Convert Excel sheets to CSV files."""
    typer.echo(f"Extracting sheets from {excel_path} to {output_dir}...")
    try:
        excel_to_csv_sheets(excel_path, output_dir=output_dir, skip_rows=skip_rows)
        typer.secho("Extraction complete.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Error converting Excel to CSV: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def process(
    csv_dir: str = typer.Option(
        "output/csv", "--csv-dir", "-i", help="Directory containing raw CSVs"
    ),
    output_dir: str = typer.Option(
        "output/ml_ready", "--output-dir", "-o", help="Directory to save processed data"
    ),
):
    """Process raw CSVs into Tidy DataFrames (Flor/Fruto) and organize by Fazenda."""
    typer.echo(f"Processing CSVs from {csv_dir}...")

    if not os.path.exists(csv_dir):
        typer.secho(f"Error: CSV directory '{csv_dir}' not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    df_flor_all, df_fruto_all = process_all_csvs(csv_dir)

    if df_flor_all.empty and df_fruto_all.empty:
        typer.secho("No data found to process.", fg=typer.colors.YELLOW)
        return

    # Identify unique fazendas
    fazendas = set()
    if not df_flor_all.empty:
        fazendas.update(df_flor_all["fazenda"].unique())
    if not df_fruto_all.empty:
        fazendas.update(df_fruto_all["fazenda"].unique())

    typer.echo(f"Found data for {len(fazendas)} fazendas: {', '.join(fazendas)}")

    os.makedirs(output_dir, exist_ok=True)

    for fazenda in fazendas:
        faz_dir = os.path.join(output_dir, fazenda)
        os.makedirs(faz_dir, exist_ok=True)

        # Filter
        df_flor = (
            df_flor_all[df_flor_all["fazenda"] == fazenda]
            if not df_flor_all.empty
            else pd.DataFrame()
        )
        df_fruto = (
            df_fruto_all[df_fruto_all["fazenda"] == fazenda]
            if not df_fruto_all.empty
            else pd.DataFrame()
        )

        # Save
        if not df_flor.empty:
            path = os.path.join(faz_dir, f"{fazenda}_flor_data.csv")
            df_flor.to_csv(path, index=False)
            typer.echo(f"  Saved: {path}")

        if not df_fruto.empty:
            path = os.path.join(faz_dir, f"{fazenda}_fruto_data.csv")
            df_fruto.to_csv(path, index=False)
            typer.echo(f"  Saved: {path}")


@app.command()
def analyze(
    ml_dir: str = typer.Option(
        "output/ml_ready", "--ml-dir", "-i", help="Directory containing processed data"
    ),
    output_dir: str = typer.Option(
        "output/analysis",
        "--output-dir",
        "-o",
        help="Directory to save analysis reports",
    ),
):
    """Generate analysis reports from processed data."""
    typer.echo(f"Looking for data in {ml_dir}...")

    if not os.path.exists(ml_dir):
        typer.secho(f"Error: ML directory '{ml_dir}' not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    found_data = False
    for item in os.listdir(ml_dir):
        faz_path = os.path.join(ml_dir, item)
        if os.path.isdir(faz_path):
            fazenda = item
            typer.echo(f"Analyzing Fazenda: {fazenda}")

            flor_path = os.path.join(faz_path, f"{fazenda}_flor_data.csv")
            fruto_path = os.path.join(faz_path, f"{fazenda}_fruto_data.csv")

            df_flor = (
                pd.read_csv(flor_path) if os.path.exists(flor_path) else pd.DataFrame()
            )
            df_fruto = (
                pd.read_csv(fruto_path)
                if os.path.exists(fruto_path)
                else pd.DataFrame()
            )

            if not df_flor.empty or not df_fruto.empty:
                found_data = True
                faz_analysis_dir = os.path.join(output_dir, fazenda)
                generate_report(df_flor, df_fruto, output_dir=faz_analysis_dir)
                typer.echo(f"  Report saved to {faz_analysis_dir}")
            else:
                typer.echo(f"  No data files found for {fazenda}")

    if not found_data:
        typer.secho("No valid data found to analyze.", fg=typer.colors.YELLOW)


@app.command()
def pipeline(
    excel_path: str = typer.Argument(..., help="Path to the input Excel file"),
    base_output: str = typer.Option(
        "output", "--base-output", "-o", help="Base directory for all outputs"
    ),
    skip_rows: int = typer.Option(0, help="Rows to skip in Excel sheets"),
):
    """
    Run the complete end-to-end pipeline (Extract -> Process -> Analyze).
    """
    csv_dir = os.path.join(base_output, "csv")
    ml_ready_dir = os.path.join(base_output, "ml_ready")
    analysis_dir = os.path.join(base_output, "analysis")

    if os.path.exists(base_output):
        typer.echo(f"Cleaning existing output directory: {base_output}")
        shutil.rmtree(base_output)

    # 1. Extract
    extract(excel_path, output_dir=csv_dir, skip_rows=skip_rows)

    # 2. Process
    process(csv_dir=csv_dir, output_dir=ml_ready_dir)

    # 3. Analyze
    analyze(ml_dir=ml_ready_dir, output_dir=analysis_dir)

    typer.secho("\n--- Pipeline completed successfully ---", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
