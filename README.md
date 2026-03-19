# 🏎️ F1 Race Viewer

**F1 Race Viewer** is an API-driven web application for visualising and analysing Formula 1 telemetry and race data.

The system integrates **FastF1** and **OpenF1** to provide synchronised race playback, telemetry exploration, and a visualisation/report builder, allowing users to generate analytical insights without directly interacting with raw API data.

---

## 🚀 Features

- **Race Playback Dashboard**  
  Reconstructs race sessions through a synchronised timeline of telemetry, timing, and race events.

- **Telemetry Visualisation**  
  Explore car data such as speed, throttle, gear, and position across a session.

- **Visualisation & Report Builder**  
  Generate analytical charts (e.g. lap times, tyre strategies) using predefined templates and export them for reporting.

- **Driver & Team Analysis**  
  View performance summaries, statistics, and season trends.

- **Data Processing Pipeline**  
  Includes telemetry downsampling and time normalisation to align heterogeneous data sources.

---

## 🏗️ Architecture

The system follows a **client–server architecture**:

### Backend (Django)
- Integrates FastF1 and OpenF1  
- Handles data retrieval, processing, and validation  
- Generates Plotly figure specifications (JSON)

### Frontend (React + TypeScript)
- Renders interactive dashboards and charts  
- Implements race playback and report builder UI  
- Manages application state and API communication  

---

## 🔗 Data Sources

- FastF1 – historical and telemetry data  
  https://github.com/theOehrly/Fast-F1  

- OpenF1 – timing, events, and race control data  
  https://github.com/br-g/openf1  

---

## ⚙️ Key Technical Concepts

- **Time Normalisation**  
  Aligns FastF1 (session-relative time) with OpenF1 (UTC timestamps)

- **Telemetry Downsampling**  
  Reduces dataset size while preserving analytical value

- **Time Binning**  
  Synchronises multi-source telemetry into fixed intervals for playback

- **Plotly Figure Generation**  
  Backend-generated chart specifications rendered dynamically in the frontend

---

## 📦 Project Structure

f1-race-viewer/
├── backend/        # Django API, telemetry processing, endpoints
├── frontend/       # React (TypeScript) application
├── api/            # Data ingestion and helper modules
└── README.md

---

## ▶️ Getting Started

### 1. Clone the repository
git clone https://github.com/yourusername/f1-race-viewer.git
cd f1-race-viewer

### 2. Backend setup
cd backend
pip install -r requirements.txt
python manage.py runserver

### 3. Frontend setup
cd frontend
npm install
npm run dev

---

## 📊 Example Use Cases

- Analyse lap-time trends and race pace  
- Compare tyre strategies across drivers  
- Reconstruct race progression through playback  
- Generate exportable charts for reports or articles  

---

## ⚠️ Limitations

- OpenF1 data is limited to **2018 onwards**  
- API rate limits may affect data availability  
- Designed as a **single-user academic prototype**  

---

## 🔮 Future Work

- Real-time race analysis via WebSocket streaming  
- Additional visualisation templates  
- Machine learning for predictive insights  
- Natural language summaries of race events  

---

## 📄 Disclaimer

This project uses publicly available Formula 1 data from FastF1 and OpenF1 for academic purposes only.  
All trademarks and data remain the property of their respective owners. No affiliation with Formula 1 is implied.

---

## 👨‍💻 Author

Albert Fernandez  
BSc Computer Science (Software Engineering)  
Keele University
