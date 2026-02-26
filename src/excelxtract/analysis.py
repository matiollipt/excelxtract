import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import os
from typing import List, Optional, Any, Dict
from .config import settings, ProcessingConfig


def set_professional_style():
    """Sets a professional style for all plots."""
    sns.set_theme(style="whitegrid", palette="viridis", context="notebook")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "font.size": 12,
            "axes.labelsize": 14,
            "axes.titlesize": 16,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "legend.fontsize": 10,
            "legend.title_fontsize": 11,
            "figure.dpi": 150,
            "savefig.bbox": "tight",
        }
    )


def _stacked_bar_plot(data, **kwargs):
    """Helper function for FacetGrid to plot stacked bars."""
    stage_cols = kwargs.pop("stage_cols")
    group_col = kwargs.pop("group_col")
    kwargs.pop(
        "color", None
    )  # Remove color passed by FacetGrid to use colormap instead

    # Aggregate data for this facet
    df_grouped = data.groupby(group_col)[stage_cols].sum()

    ax = plt.gca()
    df_grouped.plot(kind="bar", stacked=True, ax=ax, colormap="viridis", **kwargs)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize="xx-small")
    plt.xticks(rotation=45)


def plot_faceted_stacked_bars(
    df: pd.DataFrame,
    stage_cols: List[str],
    group_col: str,
    facet_col: str,
    title: str,
    output_path: str,
    row_facet: Optional[str] = None,
):
    """Generates faceted stacked bar plots. Supports 1D or 2D faceting."""
    if df.empty:
        return

    df_plot = df.copy()
    if facet_col == "date":
        df_plot["date"] = pd.to_datetime(df_plot["date"]).dt.strftime("%Y-%m-%d")
    if row_facet == "date":
        df_plot["date"] = pd.to_datetime(df_plot["date"]).dt.strftime("%Y-%m-%d")

    # Grid configuration
    cols = 2 if not row_facet else None

    g = sns.FacetGrid(
        df_plot,
        col=facet_col,
        row=row_facet,
        col_wrap=cols,
        height=5,
        aspect=1.2,
        sharex=False,
        sharey=False,
    )
    g.map_dataframe(_stacked_bar_plot, stage_cols=stage_cols, group_col=group_col)

    plt.subplots_adjust(top=0.9, right=0.85)
    g.fig.suptitle(title, fontsize=18, fontweight="bold")

    for ax in g.axes.flat:
        ax.set_xlabel(group_col.capitalize())
        ax.set_ylabel("Cumulative Counts")

    plt.savefig(output_path)
    plt.close()


def plot_complete_profile(
    df: pd.DataFrame,
    stage_cols: List[str],
    title: str,
    output_path: str,
    group_col: str = "tratamento",
):
    """Plots the aggregated stacked profile across all dates."""
    if df.empty:
        return

    df_grouped = df.groupby(group_col)[stage_cols].sum()

    fig, ax = plt.subplots(figsize=(14, 8))
    df_grouped.plot(kind="bar", stacked=True, ax=ax, colormap="viridis")

    plt.title(f"Complete Phenological Profile: {title}", fontweight="bold", pad=20)
    plt.ylabel("Cumulative Counts (Total Observation Period)")
    plt.xlabel(group_col.capitalize())
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left", title="Stages")
    plt.xticks(rotation=0)

    # Add totals on top
    totals = df_grouped.sum(axis=1)
    for i, total in enumerate(totals):
        ax.text(
            i,
            total + (total * 0.01),
            f"{int(total)}",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def perform_pca_grid(
    df: pd.DataFrame,
    stage_cols: List[str],
    title: str,
    output_path: str,
    label_col: str = "tratamento",
):
    """Performs PCA with different feature subsets."""
    if df.empty or len(df) < 5:
        return

    # Define feature subsets to iterate on
    subsets = {
        "Full Feature Set": stage_cols,
        "Core Stages (Excl. RV)": [c for c in stage_cols if c != "rv"],
        "High-Variance Stages": list(
            df[stage_cols]
            .var()
            .sort_values(ascending=False)
            .head(min(5, len(stage_cols)))
            .index
        ),
    }

    fig, axes = plt.subplots(1, 3, figsize=(22, 6))

    for i, (name, cols) in enumerate(subsets.items()):
        X = df[cols].apply(pd.to_numeric, errors="coerce").fillna(0).values
        if X.shape[1] < 2:
            axes[i].text(0.5, 0.5, "Insufficient Features", ha="center")
            continue

        X_scaled = StandardScaler().fit_transform(X)
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        var = pca.explained_variance_ratio_.sum() * 100

        scatter = sns.scatterplot(
            x=X_pca[:, 0],
            y=X_pca[:, 1],
            hue=df[label_col],
            ax=axes[i],
            palette="Set2",
            alpha=0.8,
            s=80,
            edgecolor="w",
        )
        axes[i].set_title(f"{name}\n({var:.1f}% Expl. Variance)")
        axes[i].set_xlabel("Principal Component 1")
        axes[i].set_ylabel("Principal Component 2")
        axes[i].legend(title=label_col, loc="best", fontsize="x-small")

    plt.suptitle(
        f"PCA Unsupervised Analysis Grid: {title}",
        fontsize=20,
        fontweight="bold",
        y=1.05,
    )
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def perform_tsne_grid(
    df: pd.DataFrame,
    stage_cols: List[str],
    title: str,
    output_path: str,
    label_col: str = "tratamento",
):
    """Performs t-SNE with a grid of perplexity values."""
    if df.empty or len(df) < 10:
        return

    perplexities = [5, 15, 30, 50]
    # Filter perplexities to be less than number of samples
    perplexities = [p for p in perplexities if p < len(df)]

    if not perplexities:
        return

    n_plots = len(perplexities)
    fig, axes = plt.subplots(1, n_plots, figsize=(6 * n_plots, 6))
    if n_plots == 1:
        axes = [axes]

    X = df[stage_cols].apply(pd.to_numeric, errors="coerce").fillna(0).values
    X_scaled = StandardScaler().fit_transform(X)

    for i, perp in enumerate(perplexities):
        tsne = TSNE(
            n_components=2,
            perplexity=perp,
            random_state=42,
            init="pca",
            learning_rate="auto",
        )
        X_tsne = tsne.fit_transform(X_scaled)

        sns.scatterplot(
            x=X_tsne[:, 0],
            y=X_tsne[:, 1],
            hue=df[label_col],
            ax=axes[i],
            palette="Set1",
            alpha=0.8,
            s=80,
            edgecolor="w",
        )
        axes[i].set_title(f"Perplexity: {perp}")
        axes[i].set_xlabel("Dimension 1")
        axes[i].set_ylabel("Dimension 2")
        axes[i].legend(title=label_col, loc="best", fontsize="x-small")

    plt.suptitle(
        f"t-SNE Parameter Grid Search: {title}", fontsize=20, fontweight="bold", y=1.05
    )
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def generate_report(
    df_flor: pd.DataFrame,
    df_fruto: pd.DataFrame,
    config: ProcessingConfig = settings,
    output_dir: str = "output/analysis",
    facet_col: str = "date",
    row_facet: Optional[str] = None,
) -> None:
    """Generates a comprehensive professional report."""
    print(f"Generating Advanced Analysis Report in {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    set_professional_style()

    flor_stages = config.flor_features
    fruto_stages = config.fruto_features

    # 1. Flor Analysis
    if not df_flor.empty:
        # Stacked evolution by Treatment and Facets
        plot_faceted_stacked_bars(
            df_flor,
            flor_stages,
            group_col="tratamento",
            facet_col=facet_col,
            row_facet=row_facet,
            title="Flor: Treatment Profile Evolution",
            output_path=os.path.join(output_dir, "flor_evolution.png"),
        )

        # Complete Aggregated Profile
        plot_complete_profile(
            df_flor,
            flor_stages,
            title="Flor Totals (Complete Profile)",
            output_path=os.path.join(output_dir, "flor_complete_profile.png"),
        )

        # Unsupervised Grids
        perform_pca_grid(
            df_flor,
            flor_stages,
            title="Flor PCA",
            output_path=os.path.join(output_dir, "flor_pca_grid.png"),
        )
        perform_tsne_grid(
            df_flor,
            flor_stages,
            title="Flor t-SNE",
            output_path=os.path.join(output_dir, "flor_tsne_grid.png"),
        )

    # 2. Fruto Analysis
    if not df_fruto.empty:
        # Stacked evolution by Treatment and Facets
        plot_faceted_stacked_bars(
            df_fruto,
            fruto_stages,
            group_col="tratamento",
            facet_col=facet_col,
            row_facet=row_facet,
            title="Fruto: Treatment Profile Evolution",
            output_path=os.path.join(output_dir, "fruto_evolution.png"),
        )

        # Complete Aggregated Profile
        plot_complete_profile(
            df_fruto,
            fruto_stages,
            title="Fruto Totals (Complete Profile)",
            output_path=os.path.join(output_dir, "fruto_complete_profile.png"),
        )

        # Unsupervised Grids
        perform_pca_grid(
            df_fruto,
            fruto_stages,
            title="Fruto PCA",
            output_path=os.path.join(output_dir, "fruto_pca_grid.png"),
        )
        perform_tsne_grid(
            df_fruto,
            fruto_stages,
            title="Fruto t-SNE",
            output_path=os.path.join(output_dir, "fruto_tsne_grid.png"),
        )
