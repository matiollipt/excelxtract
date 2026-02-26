import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, List, Dict, Any
from agrilyzer import PowerClient, Visualizer
from agrilyzer.agronomy import add_agronomic_features
from agrilyzer.eda import EDA
from .config import settings, ProcessingConfig
from .utils import log_info, log_success, log_error

def fetch_weather(
    lat: float, 
    lon: float, 
    start_date: str, 
    end_date: str, 
    params: Optional[List[str]] = None
) -> pd.DataFrame:
    """Fetches NASA POWER weather data."""
    client = PowerClient()
    if params is None:
        params = settings.weather_params
    
    log_info(f"Fetching weather data for ({lat}, {lon}) from {start_date} to {end_date}...")
    df = client.get_point_data(lat=lat, lon=lon, start=start_date, end=end_date, params=params)
    
    if df.empty:
        log_error("No weather data returned.")
        return df

    if df.index.name == 'date' or isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
    
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # Add agronomic features (VPD, GDD)
    df = add_agronomic_features(df, date_col='date')
    return df

def plot_dual_axis_weather(
    df_weather: pd.DataFrame, 
    farm_name: str, 
    output_dir: str,
    config: ProcessingConfig = settings
) -> str:
    """Creates a professional dual-axis plot of weather parameters."""
    viz = Visualizer(df_weather)
    dual_cfg = config.weather_dual_axis
    
    fig, ax1, ax2 = viz.plot_overlay(
        left_y_cols=dual_cfg.get("left", ["PRECTOTCORR"]),
        right_y_cols=dual_cfg.get("right", ["T2M", "VPD"]),
        title=f"Environmental Stressors: {farm_name.capitalize()}",
        figsize=(15, 8)
    )
    
    ax1.set_ylabel(dual_cfg.get("left_label", "Left Axis"))
    ax2.set_ylabel(dual_cfg.get("right_label", "Right Axis"))
    
    output_path = os.path.join(output_dir, f"{farm_name}_dual_axis_weather.png")
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close()
    return output_path

def overlay_phenology_on_weather(
    df_weather: pd.DataFrame,
    df_pheno: pd.DataFrame,
    farm_name: str,
    output_dir: str,
    pheno_col: str = "flor"  # Default to plotting 'flor' stage
) -> str:
    """
    Overlays aggregated phenological data on top of weather data.
    STEM-friendly dashboard for professional analysis.
    """
    if df_pheno.empty:
        return ""
        
    # Aggregate pheno by date
    df_pheno_daily = df_pheno.groupby('date')[pheno_col].sum().reset_index()
    df_pheno_daily['date'] = pd.to_datetime(df_pheno_daily['date'])
    
    # Merge or align
    # We'll use a twin axis for phenology on a weather plot
    sns.set_theme(style="whitegrid")
    fig, ax1 = plt.subplots(figsize=(16, 9))
    
    # Weather: Temperature on left axis
    sns.lineplot(data=df_weather, x='date', y='T2M', ax=ax1, color='orange', label='Temp (°C)', alpha=0.6)
    ax1.set_ylabel("Temperature (°C)", color='orange', fontsize=14, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='orange')
    
    # Weather: Precipitation as bars on same axis but different scale? 
    # Better use a second axis for Phenology
    ax2 = ax1.twinx()
    
    # Phenology as a filled line plot (area)
    sns.lineplot(data=df_pheno_daily, x='date', y=pheno_col, ax=ax2, color='green', label=f'Pheno: {pheno_col}', linewidth=2)
    ax2.fill_between(df_pheno_daily['date'], df_pheno_daily[pheno_col], color='green', alpha=0.2)
    ax2.set_ylabel(f"Coffee Phenology Count: {pheno_col}", color='green', fontsize=14, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='green')
    ax2.grid(False) # Clean up second grid
    
    # Add VPD on a third axis or just markers
    ax3 = ax1.twinx()
    ax3.spines['right'].set_position(('outward', 60))
    sns.lineplot(data=df_weather, x='date', y='VPD', ax=ax3, color='blue', label='VPD (kPa)', linestyle='--')
    ax3.set_ylabel("VPD (kPa)", color='blue', fontsize=14, fontweight='bold')
    ax3.tick_params(axis='y', labelcolor='blue')

    plt.title(f"Coffee Production vs Environmental Factors - {farm_name.capitalize()}", fontsize=18, fontweight='bold')
    
    # Format X axis
    import matplotlib.dates as mdates
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    
    # Combine legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines3, labels3 = ax3.get_legend_handles_labels()
    ax1.legend(lines + lines2 + lines3, labels + labels2 + labels3, loc='upper left')

    output_path = os.path.join(output_dir, f"{farm_name}_integrated_dashboard.png")
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close()
    return output_path

def create_eda_dashboard(
    df_weather: pd.DataFrame,
    df_pheno: pd.DataFrame,
    farm_name: str,
    output_dir: str,
    target_col: str = "flor"
) -> str:
    """
    Creates a comprehensive EDA dashboard using agrilyzer's EDA class.
    """
    if df_pheno.empty or df_weather.empty:
        return ""

    # Aggregate pheno by date to merge with weather
    df_pheno_daily = df_pheno.groupby('date').sum(numeric_only=True).reset_index()
    df_pheno_daily['date'] = pd.to_datetime(df_pheno_daily['date'])
    
    # Merge datasets
    df_merged = pd.merge(df_weather, df_pheno_daily, on='date', how='inner')
    
    if df_merged.empty:
        log_error(f"Merged dataset is empty for {farm_name}. Check date ranges.")
        return ""

    # Define schema for EDA
    schema = {
        "target": [target_col],
        "date": ["date"],
        "numeric": settings.weather_params + settings.flor_features,
        "id": ["fazenda"]
    }

    log_info(f"Generating EDA Dashboard for {farm_name}...")
    eda = EDA(
        df_merged, 
        schema=schema, 
        target_col=target_col, 
        date_col='date', 
        output_dir=output_dir
    )
    
    # Create the multi-panel dashboard
    weather_cols = [c for c in settings.weather_params if c in df_merged.columns]
    fig = eda.create_dashboard(
        weather_cols=weather_cols,
        corr_annot=True
    )
    
    output_path = os.path.join(output_dir, f"{farm_name}_eda_dashboard.png")
    # eda.create_dashboard saves to eda_dashboard.png by default in its output_dir, 
    # but we want a farm-specific name. 
    # The EDA class already saved it, let's just rename it if it exists.
    default_save_path = os.path.join(output_dir, "eda_dashboard.png")
    if os.path.exists(default_save_path):
        os.rename(default_save_path, output_path)
        
    return output_path

def plot_hovmoller_analysis(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    param: str,
    farm_name: str,
    output_dir: str
) -> str:
    """Creates a Hovmöller diagram for spatial-temporal weather trends."""
    client = PowerClient()
    log_info(f"Fetching expanded data for Hovmoller plot ({param}) for {farm_name}...")
    
    # NASA POWER params for the requested feature
    fetch_params = [param]
    if param == 'VPD':
        fetch_params = ["T2M", "RH2M"]
        
    df_exp = client.get_expanded_point_data(
        lat=lat, lon=lon, start=start_date, end=end_date,
        params=fetch_params, axis='lat', distance_km=50, num_points=10
    )
    
    if df_exp.empty:
        return ""
        
    if param == 'VPD':
        from agrilyzer.agronomy import compute_vpd
        df_exp['VPD'] = compute_vpd(df_exp)
        
    viz = Visualizer(df_exp)
    fig, ax = viz.plot_hovmoller(param=param, axis='lat', title=f"Spatio-temporal {param} Trend - {farm_name.capitalize()}")
    
    output_path = os.path.join(output_dir, f"{farm_name}_hovmoller_{param}.png")
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close()
    return output_path

def generate_agrilyzer_reports(
    start_date: str = "20240101",
    end_date: Optional[str] = None,
    output_dir: str = "output/analysis/agrilyzer",
    df_pheno: Optional[pd.DataFrame] = None
):
    """Main entry point for generating agrilyzer reports."""
    if end_date is None:
        end_date = pd.Timestamp.now().strftime("%Y%m%d")
    
    os.makedirs(output_dir, exist_ok=True)
    
    for farm_name, coords in settings.farms.items():
        try:
            df_w = fetch_weather(
                lat=coords['lat'], 
                lon=coords['lon'], 
                start_date=start_date, 
                end_date=end_date
            )
            
            if df_w.empty:
                continue
            
            farm_analysis_dir = os.path.join(output_dir, farm_name)
            os.makedirs(farm_analysis_dir, exist_ok=True)
            
            # 1. Standard Dual Axis Weather
            plot_dual_axis_weather(df_w, farm_name, farm_analysis_dir)
            
            # 2. Integrated Dashboard if pheno data is provided
            if df_pheno is not None:
                # Filter pheno for this farm
                farm_pheno = df_pheno[df_pheno['fazenda'].str.lower() == farm_name.lower()]
                if not farm_pheno.empty:
                    # Advanced overlay
                    overlay_phenology_on_weather(df_w, farm_pheno, farm_name, farm_analysis_dir)
                    # New EDA Dashboard from agrilyzer.eda
                    create_eda_dashboard(df_w, farm_pheno, farm_name, farm_analysis_dir)
                    log_success(f"Generated integrated dashboards for {farm_name}")

            # 3. Hovmoller Plot for temperature trends
            plot_hovmoller_analysis(
                coords['lat'], coords['lon'], 
                start_date, end_date, 
                'T2M', farm_name, farm_analysis_dir
            )
            
            # 4. Heatmaps
            viz = Visualizer(df_w)
            for param in ['T2M', 'VPD', 'PRECTOTCORR']:
                if param in df_w.columns:
                    fig = viz.plot_heatmap(col=param)
                    plt.suptitle(f"{param} Heatmap - {farm_name.capitalize()}", y=1.05)
                    plt.savefig(os.path.join(farm_analysis_dir, f"{farm_name}_{param.lower()}_heatmap.png"), bbox_inches='tight')
                    plt.close()

            log_success(f"Weather reports for {farm_name} saved to {farm_analysis_dir}")
            
        except Exception as e:
            log_error(f"Error processing weather for {farm_name}: {e}")

if __name__ == "__main__":
    generate_agrilyzer_reports()
