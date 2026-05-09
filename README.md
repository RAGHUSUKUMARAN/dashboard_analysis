# NCCC Cyber Incident Dashboard

A professional SOC-style Cyber Incident Monitoring Dashboard built using Python, Dash, Plotly, and Pandas.

The dashboard provides centralized monitoring, analytics, visualization, and reporting for cyber security incidents with an executive-level operational interface.

---

# Features

- Real-time cyber incident monitoring
- Interactive SOC dashboard
- Severity-based incident analytics
- Unit-wise incident tracking
- Threat visualization charts
- KPI cards and executive metrics
- Incident trend analysis
- PDF export support
- Excel-based data ingestion
- Multi-page responsive dashboard
- Advanced filtering and drill-down analytics

---

# Technology Stack

## Backend
- Python
- Pandas
- NumPy

## Frontend / Dashboard
- Dash
- Plotly
- Dash Bootstrap Components

## Visualization
- Plotly Graphs
- Matplotlib

## Reporting
- ReportLab
- Kaleido

---

# Project Structure

```text
dashboard_analysis/
│
├── app.py
├── callbacks.py
├── layout.py
├── loader.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── assets/
├── data/
├── exports/
├── screenshots/
└── utils/
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/RAGHUSUKUMARAN/dashboard_analysis.git
cd dashboard_analysis
```

---

## Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Run Dashboard

```bash
python app.py
```

Dashboard will start locally on:

```text
http://127.0.0.1:8050
```

---

# Dashboard Modules

- Executive Overview
- Incident Analytics
- Severity Distribution
- Trend Monitoring
- Unit-Level Monitoring
- KPI Monitoring
- Threat Statistics
- Export & Reporting

---

# Screenshots

Add dashboard screenshots inside the `screenshots/` folder.

Example:

```markdown
![Dashboard](screenshots/dashboard.png)
```

---

# Future Enhancements

- Live SIEM integration
- Real-time streaming pipeline
- Threat intelligence integration
- Automated alerting
- User authentication
- Role-based access control
- Cloud deployment
- API integration
- SOC automation workflows

---

# Deployment

This dashboard can be deployed using:

- Render
- Railway
- Heroku
- AWS EC2
- Azure App Service
- Docker

---

# Author

Raghu Sukumaran

GitHub:
https://github.com/RAGHUSUKUMARAN

---

# License

This project is intended for educational, research, and portfolio purposes.
