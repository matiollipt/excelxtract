import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import os
from typing import List, Optional, Any
from .config import settings, ProcessingConfig


def plot_stacked_stages(
    df: pd.DataFrame,
    title: str,
    stage_cols: List[str],
    group_by: str = "date",
    output_path: Optional[str] = None,
) -> None:
    """Plots stacked bars of developmental stages over time or by group.

    Args:
        df: The DataFrame containing the data.
        title: Title for the plot.
        stage_cols: List of column names representing the stages to stack.
        group_by: Column name to group data by (default: "date").
        output_path: If provided, saves the plot to this file path.
    """
    if df.empty:
        return

    # Aggregate by group_by
    df_grouped = df.groupby(group_by)[stage_cols].sum()

    # Plot
    df_grouped.plot(kind="bar", stacked=True, figsize=(12, 6), colormap="viridis")
    plt.title(f"Developmental Stages: {title} (by {group_by})")
    plt.ylabel("Counts")
    plt.xlabel(group_by)
    plt.xticks(rotation=45)
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path)
    plt.close()


def perform_unsupervised_analysis(
    df: pd.DataFrame,
    stage_cols: List[str],
    label_col: str = "tratamento",
    title: str = "Data",
    output_dir: str = "output/analysis",
) -> None:
    """Performs PCA and t-SNE clustering on stage counts and saves plots.

    Args:
        df: The DataFrame containing the data.
        stage_cols: List of feature columns to use for clustering.
        label_col: Column to use for coloring the clusters (default: "tratamento").
        title: Title for the analysis plots.
        output_dir: Directory to save the resulting plots.
    """
    if df.empty or len(df) < 2:
        return

    os.makedirs(output_dir, exist_ok=True)

    # 1. Preprocessing
    # Ensure numeric types, coercing errors to NaN then filling with 0
    X = df[stage_cols].apply(pd.to_numeric, errors="coerce").fillna(0).values
    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 2. PCA
    pca = PCA(n_components=min(2, X.shape[1]))
    X_pca = pca.fit_transform(X_scaled)
    explained_variance = pca.explained_variance_ratio_.sum() * 100

    # 3. t-SNE
    # perplexity should be smaller than number of samples
    perplexity = min(30, max(5, len(df) // 5))
    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42)
    X_tsne = tsne.fit_transform(X_scaled)

    # 4. Visualization Dashboard
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # PCA Plot
    sns.scatterplot(
        x=X_pca[:, 0],
        y=X_pca[:, 1],
        hue=df[label_col],
        ax=axes[0],
        palette="tab10",
        alpha=0.7,
    )
    axes[0].set_title(f"PCA ({explained_variance:.1f}% Variance)")
    axes[0].set_xlabel("PC1")
    axes[0].set_ylabel("PC2")

    # t-SNE Plot
    sns.scatterplot(
        x=X_tsne[:, 0],
        y=X_tsne[:, 1],
        hue=df[label_col],
        ax=axes[1],
        palette="tab10",
        alpha=0.7,
    )
    axes[1].set_title("t-SNE Clustering")
    axes[1].set_xlabel("Dim 1")
    axes[1].set_ylabel("Dim 2")

    plt.suptitle(f"Unsupervised Cluster Analysis: {title}")
    plt.tight_layout()

    if output_dir:
        plt.savefig(
            os.path.join(
                output_dir, f"{title.lower().replace(' ', '_')}_clustering.png"
            )
        )
    plt.close()


def generate_report(
    df_flor: pd.DataFrame,
    df_fruto: pd.DataFrame,
    config: ProcessingConfig = settings,
    output_dir: str = "output/analysis",
) -> None:
    """Generates a full dashboard report of the data, including stacked bars and clustering.

    Args:
        df_flor: The processed Flor DataFrame.
        df_fruto: The processed Fruto DataFrame.
        config: Configuration object containing feature lists.
        output_dir: Directory where report images will be saved.
    """
    print("Generating Analysis Report...")
    os.makedirs(output_dir, exist_ok=True)

    flor_stages = config.flor_features
    fruto_stages = config.fruto_features

    # 1. Stacked Bars
    if not df_flor.empty:
        plot_stacked_stages(
            df_flor,
            "Flor",
            flor_stages,
            group_by="date",
            output_path=os.path.join(output_dir, "flor_stages_by_date.png"),
        )
        plot_stacked_stages(
            df_flor,
            "Flor",
            flor_stages,
            group_by="tratamento",
            output_path=os.path.join(output_dir, "flor_stages_by_trat.png"),
        )

        perform_unsupervised_analysis(
            df_flor, flor_stages, title="Flor Stages Clustering", output_dir=output_dir
        )

    if not df_fruto.empty:
        plot_stacked_stages(
            df_fruto,
            "Fruto",
            fruto_stages,
            group_by="date",
            output_path=os.path.join(output_dir, "fruto_stages_by_date.png"),
        )
        plot_stacked_stages(
            df_fruto,
            "Fruto",
            fruto_stages,
            group_by="tratamento",
            output_path=os.path.join(output_dir, "fruto_stages_by_trat.png"),
        )

        perform_unsupervised_analysis(
            df_fruto,
            fruto_stages,
            title="Fruto Stages Clustering",
            output_dir=output_dir,
        )
