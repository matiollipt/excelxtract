import os
from excelxtract.agent_tools import AgrilyzerTools

def test_refined_plots():
    tools = AgrilyzerTools(output_dir="output/analysis/refined_agent_plots")
    
    farms = {
        "Vicente": {"lat": -15.399654, "lon": -39.237321},
        "Felipe": {"lat": -15.299560, "lon": -39.145943}
    }
    
    start_date = "20240101"
    end_date = "20260224"
    
    markers = [
        ("2024-01-15", "Ind. Floral 24", "blue"),
        ("2024-09-15", "Florada 24", "green"),
        ("2025-01-15", "Ind. Floral 25", "blue"),
        ("2025-05-15", "Colheita 25", "red"),
        ("2025-09-15", "Florada 25", "green"),
        ("2026-05-15", "Colheita 26 (Est.)", "red"),
    ]
    
    for farm_name, coords in farms.items():
        print(f"\n--- Testing Refined Plots for {farm_name} ---")
        
        # 1. Fetch Data
        df = tools.fetch_weather_data(
            lat=coords["lat"], 
            lon=coords["lon"], 
            start_date=start_date, 
            end_date=end_date
        )
        
        if df.empty:
            continue
            
        # 2. Single Axis: Agronomic Features
        tools.plot_single_axis(
            df=df,
            cols=["T2M", "VPD", "RH2M"],
            title=f"Refined Agronomic Profile - {farm_name}",
            filename=f"{farm_name.lower()}_agronomic_ts.png",
            markers=markers
        )
        
        # 3. Dual Axis: Precipitation vs VPD
        tools.plot_dual_axis(
            df=df,
            left_cols=["PRECTOTCORR"],
            right_cols=["VPD"],
            title=f"Precipitation and VPD Dynamics - {farm_name}",
            filename=f"{farm_name.lower()}_precip_vpd.png",
            left_label="Precipitation (mm/day)",
            right_label="VPD (kPa)",
            markers=markers
        )
        
        # 4. Hovmoller: VPD along Latitude (showing spatial gradient around the farm)
        tools.plot_hovmoller(
            lat=coords["lat"],
            lon=coords["lon"],
            start_date=start_date,
            end_date=end_date,
            param="VPD",
            filename=f"{farm_name.lower()}_vpd_hovmoller.png",
            axis="lat",
            distance_km=30.0,
            num_points=10
        )
        
        # 5. Heatmap: Solar Irradiance
        tools.plot_heatmap(
            df=df,
            col="ALLSKY_SFC_SW_DWN",
            title=f"Solar Irradiance (SW Downward) - {farm_name}",
            filename=f"{farm_name.lower()}_solar_heatmap.png"
        )

if __name__ == "__main__":
    test_refined_plots()
