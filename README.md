# 🏎️ F1 Race Viewer

**F1 Race Viewer** is a full-stack, API-driven web application for visualising and analysing Formula 1 telemetry and race data.

The platform integrates **FastF1** and **OpenF1** to provide synchronised race playback, telemetry exploration, and a visualisation/report builder, allowing users to generate analytical insights without directly interacting with raw API data.

🌐 **Live Application:** https://f1raceviewer.albertfernandez.dev

---

## 🚀 Features

- **Race Playback Dashboard**  
  Reconstructs race sessions through a synchronised timeline of telemetry, timing, and race events.

- **Telemetry Visualisation**  
  Explore car data such as speed, throttle, gear, gear shifts, and track position across a session.

- **Visualisation & Report Builder**  
  Generate analytical charts (e.g. lap times, tyre strategies) using predefined templates and export them for reporting.

- **Driver & Team Analysis**  
  View performance summaries, statistics, and season trends.

- **Data Processing Pipeline**  
  Includes telemetry downsampling and time normalisation to align heterogeneous data sources.

---

## 🏗️ Architecture

The system follows a **containerised client–server architecture**, deployed to a Linux VPS using Docker.

### Frontend (React + TypeScript + Nginx)

- Interactive dashboards and telemetry UI
- Race playback controls and report builder
- API communication with backend services
- Served through Nginx in a Docker container

### Backend (Django REST API)

- Integrates FastF1 and OpenF1
- Handles data retrieval, transformation, and validation
- Generates Plotly chart specifications (JSON)
- Exposes REST endpoints consumed by the frontend

### Deployment Infrastructure

- Docker Compose multi-container setup
- Reverse proxy with SSL/TLS
- Public production hosting on custom subdomain

---

## 🔗 Data Sources

- **FastF1** – historical race and telemetry data  
  https://github.com/theOehrly/Fast-F1

- **OpenF1** – live timing, events, and race control data  
  https://github.com/br-g/openf1

---

## ⚙️ Key Technical Concepts

- **Time Normalisation**  
  Aligns FastF1 (session-relative timing) with OpenF1 (UTC timestamps)

- **Telemetry Downsampling**  
  Reduces payload size while preserving analytical value

- **Time Binning**  
  Synchronises multi-source telemetry into fixed playback intervals

- **Backend Chart Generation**  
  Plotly figure JSON generated server-side and rendered dynamically client-side

- **Containerised Deployment**  
  Frontend and backend isolated into dedicated services

---

## 📦 Project Structure

```text
f1raceviewer/
├── backend/        # Django API, telemetry processing, endpoints
├── frontend/       # React + TypeScript application
├── docker-compose.yml
└── README.md
```

---

## ▶️ Running Locally (Development)

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/f1-race-viewer.git
cd f1-race-viewer
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
python manage.py runserver
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🐳 Production Deployment

The production version is deployed using Docker Compose with separate frontend and backend containers.

### Services

- **Frontend:** React static build served by Nginx
- **Backend:** Django + Gunicorn
- **Reverse Proxy:** HTTPS routing and SSL termination

### Live URL

https://f1raceviewer.albertfernandez.dev

---

## 📊 Example Use Cases

- Analyse lap-time trends and race pace
- Compare tyre strategies across drivers
- Reconstruct race progression through playback
- Generate exportable charts for reports or articles
- Inspect telemetry traces for individual laps

---

## ⚠️ Limitations

- Race Playback feature is limited to **2023 onwards**
- Third-party API rate limits may affect responsiveness
- Academic prototype focused on analysis rather than commercial scalability

---

## 🔮 Future Work

- Real-time race analysis via WebSocket streaming
- User accounts and saved reports
- Additional visualisation templates
- Predictive modelling / machine learning insights
- Natural language summaries of race events

---

## 📄 Disclaimer

This project uses publicly available Formula 1 data from FastF1 and OpenF1 for academic purposes only.

All trademarks, branding, and data remain the property of their respective owners. No affiliation with Formula 1 is implied.

---

## 👨‍💻 Author

**Albert Fernandez**  
BSc Computer Science (Software Engineering)  
Keele University
