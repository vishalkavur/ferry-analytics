# ⛴️ Ferry Capacity Utilization & Operational Efficiency Analytics

A Streamlit dashboard for analyzing ferry operations at the Jack Layton Ferry Terminal, Toronto (2015–2025).

## Live Demo
🔗 [View on Streamlit Cloud](https://your-app-url.streamlit.app)

## Features
- **KPI Summary Cards** — Capacity Utilization Ratio, Congestion Pressure Index, Idle Capacity %, Peak Strain Duration, Operational Variability
- **Utilization Timeline** — OLI trend with congestion/idle zone shading, year-over-year comparison
- **Congestion & Idle Heatmap** — Hour × Day-of-week OLI heatmap with hourly and monthly breakdowns
- **Seasonal Efficiency** — Weekday vs weekend OLI, sales vs redemptions by season, time-band analysis
- **Alerts & Summary** — Threshold-triggered alerts, efficiency summary table, filtered data download

## Dataset
Toronto Island Ferry Ticket data — 261,538 records at 15-minute intervals (2015–2025).  
Source: Toronto Open Data / Unified Mentor project.

Columns: `_id`, `Timestamp`, `Sales Count`, `Redemption Count`

## Derived Features
| Feature | Formula |
|---|---|
| Total Activity | Sales Count + Redemption Count |
| Redemption Pressure Ratio | Redemption Count / (Sales Count + 1) |
| Operational Load Index (OLI) | Normalized interval-level load (0–100%) |
| Season | Derived from month |

## Setup & Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/ferry-analytics.git
cd ferry-analytics

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## Deploy to Streamlit Cloud
1. Push this repo to GitHub (include the CSV file)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub → select repo → set `app.py` as main file
4. Click **Deploy**

## Project Structure
```
ferry-analytics/
├── app.py                          ← Main Streamlit application
├── Toronto_Island_Ferry_Tickets.csv ← Dataset
├── requirements.txt                ← Python dependencies
└── README.md                       ← This file
```

## Analytical Methodology
1. Data ingested and timestamps parsed to datetime
2. Features engineered: OLI (rolling-normalised load index), season, time bands
3. Multi-resolution aggregation: 15-min, hourly, daily
4. KPIs computed: utilization ratio, congestion pressure, idle %, peak strain duration, variability score
5. Visualizations: timeline, heatmap, seasonal comparison, alert triggers

## Built With
- [Streamlit](https://streamlit.io) — dashboard framework
- [Plotly](https://plotly.com) — interactive charts
- [Pandas](https://pandas.pydata.org) — data processing

---
*Project by Vk · Unified Mentor Internship · Toronto Government Parks, Forestry & Recreation*
