import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Ferry Capacity Analytics",
    page_icon="⛴️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    div[data-testid="metric-container"] {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 12px 16px;
    }
    .alert-high  { background:#fff0f0; border-left:4px solid #dc3545;
                   padding:10px 14px; border-radius:6px; margin-bottom:8px; }
    .alert-warn  { background:#fff8e1; border-left:4px solid #fd7e14;
                   padding:10px 14px; border-radius:6px; margin-bottom:8px; }
    .alert-good  { background:#f0fff4; border-left:4px solid #28a745;
                   padding:10px 14px; border-radius:6px; margin-bottom:8px; }
    .alert-title { font-weight:600; font-size:0.85rem; margin-bottom:2px; }
    .alert-body  { font-size:0.78rem; color:#555; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(BASE_DIR, "Toronto_Island_Ferry_Tickets.csv")
    df = pd.read_csv(csv_path)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values("Timestamp").reset_index(drop=True)

    df["Total_Activity"]      = df["Sales Count"] + df["Redemption Count"]
    df["Redemption_Pressure"] = df["Redemption Count"] / (df["Sales Count"] + 1)
    df["Year"]                = df["Timestamp"].dt.year.astype(int)
    df["Month"]               = df["Timestamp"].dt.month.astype(int)
    df["Month_Name"]          = df["Timestamp"].dt.strftime("%b")
    df["Hour"]                = df["Timestamp"].dt.hour.astype(int)
    df["DayOfWeek"]           = df["Timestamp"].dt.dayofweek.astype(int)
    df["DayName"]             = df["Timestamp"].dt.strftime("%a")
    df["IsWeekend"]           = df["DayOfWeek"] >= 5
    df["Date"]                = df["Timestamp"].dt.date

    month_to_season = {
        12:"Winter", 1:"Winter",  2:"Winter",
         3:"Spring", 4:"Spring",  5:"Spring",
         6:"Summer", 7:"Summer",  8:"Summer",
         9:"Fall",  10:"Fall",   11:"Fall"
    }
    df["Season"] = df["Month"].map(month_to_season)

    rolling_max = df["Total_Activity"].rolling(window=672, min_periods=1).max()
    df["OLI"] = (df["Total_Activity"] / rolling_max.clip(lower=1) * 100).clip(0, 100)
    df["Is_Idle"] = df["OLI"] < 15

    return df


def resample_df(df, gran):
    freq = {"15-minute": "15min", "Hourly": "h", "Daily": "D"}[gran]
    agg = (df.set_index("Timestamp")
             .resample(freq)
             .agg(Sales=("Sales Count", "sum"),
                  Redemptions=("Redemption Count", "sum"),
                  OLI=("OLI", "mean"))
             .reset_index())
    agg["Total"] = agg["Sales"] + agg["Redemptions"]
    return agg


df_full = load_data()


with st.sidebar:
    st.markdown("## ⛴️ Ferry Analytics")
    st.markdown("*Jack Layton Ferry Terminal*")
    st.divider()

    year_list = sorted(df_full["Year"].unique().tolist(), reverse=True)
    year_opts = ["All years"] + [str(y) for y in year_list]
    sel_year  = st.selectbox("📅 Year", year_opts)

    season_opts = ["All seasons", "Summer", "Spring", "Fall", "Winter"]
    sel_season  = st.selectbox("🍂 Season", season_opts)

    day_opts = ["All days", "Weekdays only", "Weekends only"]
    sel_day  = st.selectbox("📆 Day type", day_opts)

    granularity = st.selectbox("⏱ Granularity", ["Hourly", "15-minute", "Daily"])

    oli_threshold  = st.slider("🚨 Congestion OLI threshold (%)", 50, 95, 80, 5)
    idle_threshold = st.slider("💤 Idle OLI threshold (%)", 5, 40, 15, 5)

    st.divider()
    st.caption("Data: 2015–2025 · 261,538 intervals")


df = df_full.copy()
if sel_year != "All years":
    df = df[df["Year"] == int(sel_year)]
if sel_season != "All seasons":
    df = df[df["Season"] == sel_season]
if sel_day == "Weekdays only":
    df = df[~df["IsWeekend"]]
elif sel_day == "Weekends only":
    df = df[df["IsWeekend"]]


st.title("⛴️ Ferry Capacity Utilization & Operational Efficiency")

label_parts = []
if sel_year != "All years":     label_parts.append(str(sel_year))
if sel_season != "All seasons": label_parts.append(sel_season)
if sel_day != "All days":       label_parts.append(sel_day)
label_parts.append(granularity)
st.caption("  ·  ".join(label_parts) + f"  ·  {len(df):,} intervals loaded")


st.subheader("Key Performance Indicators")

if len(df) == 0:
    st.warning("No data for the selected filters.")
    st.stop()

total_intervals  = len(df)
congestion_count = int((df["OLI"] >= oli_threshold).sum())
idle_count       = int((df["OLI"] <= idle_threshold).sum())
util_ratio       = float(df["OLI"].mean())
congestion_pi    = congestion_count / total_intervals * 100
idle_pct         = idle_count / total_intervals * 100
op_var           = float(df["OLI"].std())

oli_flags = (df["OLI"] >= oli_threshold).astype(int).tolist()
runs, count = [], 0
for v in oli_flags:
    if v:
        count += 1
    else:
        if count:
            runs.append(count)
        count = 0
if count:
    runs.append(count)
peak_strain_h = round(max(runs) * 0.25, 1) if runs else 0.0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Capacity Util. Ratio",     f"{util_ratio:.1f}%")
col2.metric("Congestion Pressure Index",f"{congestion_pi:.1f}%")
col3.metric("Idle Capacity %",          f"{idle_pct:.1f}%")
col4.metric("Peak Strain Duration",     f"{peak_strain_h}h")
col5.metric("Operational Variability",  f"{op_var:.1f}")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Utilization Timeline",
    "🔥 Congestion & Idle Heatmap",
    "🍂 Seasonal Efficiency",
    "⚠️ Alerts & Summary"
])


with tab1:
    st.subheader("Capacity Utilization Timeline")
    ts_df = resample_df(df, granularity)

    series_choice = st.radio(
        "Series",
        ["OLI (%)", "Sales Count", "Redemption Count", "Total Activity"],
        horizontal=True
    )
    y_col = {"OLI (%)":"OLI","Sales Count":"Sales",
              "Redemption Count":"Redemptions","Total Activity":"Total"}[series_choice]

    fig = go.Figure()
    if series_choice == "OLI (%)":
        fig.add_hrect(y0=oli_threshold, y1=100,
                      fillcolor="rgba(220,53,69,0.07)", line_width=0,
                      annotation_text="Congestion zone",
                      annotation_position="top left",
                      annotation_font_size=11)
        fig.add_hrect(y0=0, y1=idle_threshold,
                      fillcolor="rgba(40,167,69,0.07)", line_width=0,
                      annotation_text="Idle zone",
                      annotation_position="bottom left",
                      annotation_font_size=11)
        fig.add_hline(y=oli_threshold, line_dash="dot",
                      line_color="rgba(220,53,69,0.5)", line_width=1)

    fig.add_trace(go.Scatter(
        x=ts_df["Timestamp"], y=ts_df[y_col],
        mode="lines", name=series_choice,
        line=dict(color="#1a6db5", width=1.5),
        fill="tozeroy", fillcolor="rgba(26,109,181,0.08)"
    ))
    fig.update_layout(
        height=400, margin=dict(l=0,r=0,t=10,b=0),
        xaxis_title=None, yaxis_title=series_choice,
        hovermode="x unified", plot_bgcolor="white",
        yaxis=dict(gridcolor="#f0f0f0"),
        xaxis=dict(gridcolor="#f0f0f0")
    )
    st.plotly_chart(fig, use_container_width=True)

    if sel_year == "All years":
        st.subheader("Year-over-year OLI trend")
        yearly = df_full.groupby("Year")["OLI"].mean().reset_index()
        yearly["Year"] = yearly["Year"].astype(str)
        fig2 = px.bar(yearly, x="Year", y="OLI",
                      color="OLI",
                      color_continuous_scale=["#5cb85c","#f0ad4e","#d9534f"],
                      labels={"OLI":"Mean OLI (%)"}, text_auto=".1f")
        fig2.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0),
                           showlegend=False, plot_bgcolor="white",
                           coloraxis_showscale=False)
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)


with tab2:
    st.subheader("Congestion & Idle Period Heatmap")
    st.caption("Average OLI by hour of day and day of week")

    heat_df    = df.groupby(["DayOfWeek","Hour"])["OLI"].mean().reset_index()
    heat_pivot = heat_df.pivot(index="DayOfWeek", columns="Hour", values="OLI")
    day_labels = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    heat_pivot.index = [day_labels[i] for i in heat_pivot.index]

    fig3 = px.imshow(
        heat_pivot,
        color_continuous_scale=["#d4edda","#fff3cd","#f8d7da","#dc3545"],
        range_color=[0, 100],
        labels=dict(x="Hour of day", y="", color="OLI (%)"),
        aspect="auto"
    )
    fig3.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig3, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("OLI by hour of day")
        hourly_avg = df.groupby("Hour")["OLI"].mean().reset_index()
        colors_h   = ["#dc3545" if v >= oli_threshold else
                      "#fd7e14" if v >= 50 else "#28a745"
                      for v in hourly_avg["OLI"]]
        fig4 = go.Figure(go.Bar(
            x=hourly_avg["Hour"], y=hourly_avg["OLI"].round(1),
            marker_color=colors_h,
            text=hourly_avg["OLI"].round(1),
            textposition="outside"
        ))
        fig4.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0),
                           xaxis_title="Hour", yaxis_title="Mean OLI (%)",
                           plot_bgcolor="white",
                           yaxis=dict(gridcolor="#f0f0f0"),
                           showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

    with c2:
        st.subheader("OLI by month")
        monthly = (df.groupby(["Month","Month_Name"])["OLI"]
                     .mean().reset_index().sort_values("Month"))
        fig5 = go.Figure(go.Bar(
            x=monthly["Month_Name"], y=monthly["OLI"].round(1),
            marker_color="#1a6db5",
            text=monthly["OLI"].round(1),
            textposition="outside"
        ))
        fig5.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0),
                           xaxis_title=None, yaxis_title="Mean OLI (%)",
                           plot_bgcolor="white",
                           yaxis=dict(gridcolor="#f0f0f0"),
                           showlegend=False)
        st.plotly_chart(fig5, use_container_width=True)


with tab3:
    st.subheader("Seasonal Efficiency Comparison")
    season_order = ["Winter","Spring","Summer","Fall"]

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### Weekday vs weekend OLI by season")
        seasonal = df.groupby(["Season","IsWeekend"])["OLI"].mean().reset_index()
        seasonal["Day type"] = seasonal["IsWeekend"].map({True:"Weekend",False:"Weekday"})
        seasonal["Season"]   = pd.Categorical(seasonal["Season"],
                                              categories=season_order, ordered=True)
        seasonal = seasonal.sort_values("Season")
        fig6 = px.bar(seasonal, x="Season", y="OLI", color="Day type",
                      barmode="group", text_auto=".1f",
                      color_discrete_map={"Weekday":"#1a6db5","Weekend":"#1d9e75"},
                      labels={"OLI":"Mean OLI (%)"})
        fig6.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0),
                           plot_bgcolor="white", yaxis=dict(gridcolor="#f0f0f0"),
                           legend=dict(orientation="h", yanchor="bottom", y=1.02))
        fig6.update_traces(textposition="outside")
        st.plotly_chart(fig6, use_container_width=True)

    with c2:
        st.markdown("##### Sales vs Redemptions by season")
        sr = df.groupby("Season").agg(
            Sales=("Sales Count","sum"),
            Redemptions=("Redemption Count","sum")
        ).reset_index()
        sr["Season"] = pd.Categorical(sr["Season"],
                                      categories=season_order, ordered=True)
        sr = sr.sort_values("Season")
        fig7 = go.Figure()
        fig7.add_trace(go.Bar(name="Sales", x=sr["Season"], y=sr["Sales"],
                              marker_color="#1a6db5"))
        fig7.add_trace(go.Bar(name="Redemptions", x=sr["Season"], y=sr["Redemptions"],
                              marker_color="#fd7e14"))
        fig7.update_layout(barmode="group", height=300,
                           margin=dict(l=0,r=0,t=10,b=0),
                           plot_bgcolor="white", yaxis=dict(gridcolor="#f0f0f0"),
                           legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig7, use_container_width=True)

    st.markdown("##### Morning / Afternoon / Evening efficiency bands")

    def time_band(h):
        if   6 <= h < 12: return "Morning (6-12)"
        elif 12 <= h < 17: return "Afternoon (12-17)"
        elif 17 <= h < 21: return "Evening (17-21)"
        else:              return "Off-hours"

    df_band         = df.copy()
    df_band["Band"] = df_band["Hour"].apply(time_band)
    band_season     = df_band.groupby(["Season","Band"])["OLI"].mean().reset_index()
    band_season["Season"] = pd.Categorical(band_season["Season"],
                                           categories=season_order, ordered=True)
    band_season = band_season.sort_values("Season")
    fig8 = px.bar(band_season, x="Season", y="OLI", color="Band",
                  barmode="group", text_auto=".1f",
                  labels={"OLI":"Mean OLI (%)"},
                  color_discrete_sequence=["#1a6db5","#fd7e14","#28a745","#adb5bd"])
    fig8.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0),
                       plot_bgcolor="white", yaxis=dict(gridcolor="#f0f0f0"),
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    fig8.update_traces(textposition="outside")
    st.plotly_chart(fig8, use_container_width=True)


with tab4:
    st.subheader("Threshold-based Efficiency Alerts")

    cong_df = df[df["OLI"] >= oli_threshold]
    if len(cong_df) > 0:
        top_cong = (cong_df.groupby(["Hour","DayName"])["OLI"]
                    .mean().reset_index()
                    .sort_values("OLI", ascending=False)
                    .head(3))
        for _, row in top_cong.iterrows():
            st.markdown(f"""
            <div class='alert-high'>
              <div class='alert-title'>🔴 High congestion — {row['DayName']}s at {int(row['Hour']):02d}:00</div>
              <div class='alert-body'>Mean OLI: {row['OLI']:.1f}% — exceeds threshold of {oli_threshold}%</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class='alert-good'>
            <div class='alert-title'>✅ No congestion intervals for current filters.</div>
        </div>""", unsafe_allow_html=True)

    idle_df = df[df["OLI"] <= idle_threshold]
    if len(idle_df) > 0:
        top_idle = (idle_df.groupby(["Hour","DayName"])["OLI"]
                    .mean().reset_index()
                    .sort_values("OLI")
                    .head(3))
        for _, row in top_idle.iterrows():
            st.markdown(f"""
            <div class='alert-warn'>
              <div class='alert-title'>🟡 Idle capacity — {row['DayName']}s at {int(row['Hour']):02d}:00</div>
              <div class='alert-body'>Mean OLI: {row['OLI']:.1f}% — below idle threshold of {idle_threshold}%</div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    st.subheader("Efficiency Summary Table")

    summary = df.groupby("Season").agg(
        Mean_OLI         =("OLI", "mean"),
        Max_OLI          =("OLI", "max"),
        Congestion_pct   =("OLI", lambda x: (x >= oli_threshold).mean() * 100),
        Idle_pct         =("OLI", lambda x: (x <= idle_threshold).mean() * 100),
        Total_Sales      =("Sales Count", "sum"),
        Total_Redemptions=("Redemption Count", "sum")
    ).reset_index().round(1)

    summary.columns = [
        "Season", "Mean OLI (%)", "Max OLI (%)",
        f"Congestion % (>={oli_threshold})",
        f"Idle % (<={idle_threshold})",
        "Total Sales", "Total Redemptions"
    ]
    summary["Season"] = pd.Categorical(
        summary["Season"],
        categories=["Winter","Spring","Summer","Fall"],
        ordered=True
    )
    summary = summary.sort_values("Season")
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Raw data explorer")

    n_rows    = st.slider("Rows to preview", 50, 500, 100, 50)
    show_cols = st.multiselect(
        "Columns", df.columns.tolist(),
        default=["Timestamp","Sales Count","Redemption Count",
                 "Total_Activity","OLI","Season"]
    )
    if show_cols:
        st.dataframe(df[show_cols].head(n_rows),
                     use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download filtered data as CSV",
            data=df[show_cols].to_csv(index=False),
            file_name="ferry_filtered_data.csv",
            mime="text/csv"
        )
