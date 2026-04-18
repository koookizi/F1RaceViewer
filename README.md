# 🏎️ F1 Race Viewer

**F1 Race Viewer** is a full-stack, API-driven web application for visualising and analysing Formula 1 telemetry and race data.

This branch is configured for **local development**, allowing the frontend and backend to run directly on a local machine without Docker deployment.

The platform integrates **FastF1** and **OpenF1** to provide synchronised race playback, telemetry exploration, and a visualisation/report builder.

---

## 🚀 Features

- Race Playback Dashboard
- Telemetry Visualisation
- Driver & Team Analysis
- Report / Chart Builder
- Historical Race Data Exploration
- FastF1 + OpenF1 Integration

---

## 🏗️ Architecture

### Frontend

- React
- TypeScript
- Runs locally using Vite development server

### Backend

- Django REST API
- FastF1 data processing
- OpenF1 API integration
- Runs locally using Django development server

---

## 📦 Project Structure

```text
f1raceviewer/
├── backend/
├── frontend/
└── README.md
```

---

## ▶️ Getting Started (Local Development)

## 1. Clone Repository

```bash
git clone https://github.com/yourusername/f1-race-viewer.git
cd f1-race-viewer
```

---

## 2. Backend Setup

```bash
cd backend
python -m venv env
```

### Activate Virtual Environment

#### Windows

```bash
env\Scripts\activate
```

#### Linux / macOS

```bash
source env/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Backend

```bash
python manage.py migrate
python manage.py runserver
```

Backend runs at:

```text
http://localhost:8000
```

---

## 3. Frontend Setup

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

(or another Vite port if prompted)

---

## 🔗 Frontend API Configuration

This branch expects the backend to run locally.

Example frontend requests:

```ts
fetch("http://localhost:8000/api/seasons_years/")
```

or with a config variable:

```ts
const API_BASE = "http://localhost:8000/api";
```

---

## 📊 Example Use Cases

- Replay races with synced telemetry
- Compare driver pace
- Generate lap time charts
- Analyse tyre strategies
- Explore historical telemetry datasets

---

## ⚠️ Notes

- Requires internet connection for external API data
- FastF1 may cache downloaded sessions locally
- Intended for development / local testing

---

## 🔮 Future Work

- Docker deployment branch
- User authentication
- Saved reports
- Live race mode
- Predictive analytics

---

## 👨‍💻 Author

**Albert Fernandez**  
BSc Computer Science (Software Engineering)  
Keele University
