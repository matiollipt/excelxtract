import os
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Optional, Tuple, Literal, Dict, Any
from agrilyzer import PowerClient, Visualizer
from agrilyzer.agronomy import add_agronomic_features
from .utils import log_info, log_success, log_error

class AgrilyzerTools:
    """
    A collection of tools for fetching and visualizing environmental data using agrilyzer.
    Designed for agentic use.
    """

    def __init__(self, output_dir: str = "output/analysis/agent_tools"):
        self.client = PowerClient()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_weather_data(
        self, 
        lat: float, 
        lon: float, 
        start_date: str, 
        end_date: str, 
        params: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Fetches daily weather data for a specific coordinate and date range.
        
        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date in YYYYMMDD format.
            end_date: End date in YYYYMMDD format.
            params: List of NASA POWER parameters. Defaults to a standard set.
            
        Returns:
            pd.DataFrame with weather data.
        """
        if params is None:
            params = ["T2M", "T2M_MAX", "T2M_MIN", "RH2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN"]
        
        log_info(f"Fetching weather data for ({lat}, {lon}) from {start_date} to {end_date}...")
        df = self.client.get_point_data(lat=lat, lon=lon, start=start_date, end=end_date, params=params)
        
        if df.empty:
            log_error("No data returned from API.")
            return df
            
        # Standardize for agrilyzer
        if df.index.name == 'date' or isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            
        # Add agronomic features (VPD, GDD)
        from agrilyzer.agronomy import compute_vpd
        df['VPD'] = compute_vpd(df)
        df = add_agronomic_features(df)
        log_success(f"Fetched {len(df)} days of data.")
        return df

    def _add_markers(self, ax, df: pd.DataFrame, markers: Optional[List[Tuple[str, str, str]]]):
        """Internal helper to add vertical marker lines to a plot."""
        if not markers:
            return
            
        for date_str, label, color in markers:
            try:
                d = pd.to_datetime(date_str)
                if d >= df['date'].min() and d <= df['date'].max():
                    ax.axvline(x=d, color=color, linestyle="--", alpha=0.6)
                    ax.text(d, ax.get_ylim()[1], label, rotation=90, 
                            verticalalignment='top', fontsize=8, color=color)
            except Exception as e:
                log_error(f"Error adding marker {label}: {e}")

    def plot_single_axis(
        self, 
        df: pd.DataFrame, 
        cols: List[str], 
        title: str, 
        filename: str,
        markers: Optional[List[Tuple[str, str, str]]] = None
    ) -> str:
        """
        Creates a single-axis time series plot.
        
        Args:
            df: The weather DataFrame.
            cols: Columns to plot.
            title: Plot title.
            filename: Output filename (within output_dir).
            markers: Optional list of (date_str, label, color) for vertical lines.
            
        Returns:
            Path to the saved plot.
        """
        viz = Visualizer(df)
        fig, ax = viz.plot_timeseries(cols=cols, title=title, figsize=(15, 8))
        
        self._add_markers(ax, df, markers)

        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        log_success(f"Single-axis plot saved to {output_path}")
        return output_path

    def plot_dual_axis(
        self, 
        df: pd.DataFrame, 
        left_cols: List[str], 
        right_cols: List[str], 
        title: str, 
        filename: str,
        left_label: str = "Left Axis",
        right_label: str = "Right Axis",
        markers: Optional[List[Tuple[str, str, str]]] = None
    ) -> str:
        """
        Creates a dual-axis plot.
        
        Args:
            df: The weather DataFrame.
            left_cols: Columns for the left Y-axis.
            right_cols: Columns for the right Y-axis.
            title: Plot title.
            filename: Output filename.
            left_label: Label for the left axis.
            right_label: Label for the right axis.
            markers: Optional list of (date_str, label, color) for vertical lines.
            
        Returns:
            Path to the saved plot.
        """
        viz = Visualizer(df)
        fig, ax1, ax2 = viz.plot_overlay(
            left_y_cols=left_cols, 
            right_y_cols=right_cols, 
            title=title, 
            figsize=(15, 8)
        )
        ax1.set_ylabel(left_label)
        ax2.set_ylabel(right_label)
        
        self._add_markers(ax1, df, markers)
        
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        log_success(f"Dual-axis plot saved to {output_path}")
        return output_path

    def plot_hovmoller(
        self, 
        lat: float, 
        lon: float, 
        start_date: str, 
        end_date: str, 
        param: str, 
        filename: str,
        axis: Literal['lat', 'lon'] = 'lat',
        distance_km: float = 20.0,
        num_points: int = 15
    ) -> str:
        """
        Creates a Hovmöller diagram by fetching expanded spatial data.
        
        Args:
            lat: Center latitude.
            lon: Center longitude.
            start_date: Start date YYYYMMDD.
            end_date: End date YYYYMMDD.
            param: Parameter to plot (e.g., 'T2M', 'VPD').
            filename: Output filename.
            axis: Axis to expand along ('lat' or 'lon').
            distance_km: Total distance to cover.
            num_points: Number of points along the axis.
            
        Returns:
            Path to the saved plot.
        """
        log_info(f"Fetching expanded data for Hovmoller plot ({param})...")
        # Ensure the parameter is fetched
        params = [param]
        if param == 'VPD':
            # VPD needs T2M and RH2M
            params = ["T2M", "RH2M"]
            
        df_expanded = self.client.get_expanded_point_data(
            lat=lat, lon=lon, start=start_date, end=end_date, 
            params=params, axis=axis, distance_km=distance_km, num_points=num_points
        )
        
        if df_expanded.empty:
            log_error("No expanded data returned for Hovmoller.")
            return ""
            
        if param == 'VPD':
            from agrilyzer.agronomy import compute_vpd
            df_expanded['VPD'] = compute_vpd(df_expanded)
            
        viz = Visualizer(df_expanded)
        fig, ax = viz.plot_hovmoller(param=param, axis=axis, title=f"Hovmoller Diagram - {param}")
        
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        log_success(f"Hovmoller plot saved to {output_path}")
        return output_path

    def plot_heatmap(self, df: pd.DataFrame, col: str, title: str, filename: str) -> str:
        """Creates a calendar heatmap for a parameter."""
        viz = Visualizer(df)
        fig = viz.plot_heatmap(col=col)
        plt.suptitle(title, y=1.05, fontsize=16, fontweight='bold')
        
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        log_success(f"Heatmap saved to {output_path}")
        return output_path
