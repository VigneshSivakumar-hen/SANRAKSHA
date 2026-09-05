# 🏔️ SANRAKSHA
### AI-Powered Landslide Prediction & Early Warning System

*Smart India Hackathon 2026 – Problem Statement 26001*

SANRAKSHA is an AI-powered landslide risk monitoring and early-warning platform designed to monitor vulnerable mountainous regions and provide timely, localized risk information.

The platform combines IoT sensor data, rainfall information, terrain-related features, historical landslide data, and machine-learning-based risk prediction to estimate landslide risk for monitored locations.

## 🌐 Live Demo

| | |
|---|---|
| **Dashboard** | [sanraksha-frontend.onrender.com](https://sanraksha-frontend.onrender.com) |
| **API docs** (Swagger) | [sanraksha-backend.onrender.com/docs](https://sanraksha-backend.onrender.com/docs) |
| **API health check** | [sanraksha-backend.onrender.com/health](https://sanraksha-backend.onrender.com/health) |

> The backend runs on Render's free tier and sleeps after 15 minutes of no traffic — the first request after a quiet period can take 30–50 seconds to wake it up. That's expected, not a bug.

## 🚨 Problem

Landslides in mountainous regions can cause:

- Loss of life
- Road blockages
- Infrastructure damage
- Communication disruption
- Delayed emergency response

Conventional monitoring approaches may be difficult to deploy at a local level and may not provide sufficiently localized and timely risk information.

SANRAKSHA aims to provide a scalable monitoring and early-warning platform using AI, IoT, MQTT, and geospatial technologies.

## 💡 Solution

SANRAKSHA follows a continuous monitoring pipeline:

```
IoT Sensors / Data Sources
          ↓
       MQTT
          ↓
    IoT Gateway
          ↓
     FastAPI Backend
          ↓
     ML Risk Model
          ↓
 Risk Score + Risk Level
          ↓
    React Dashboard
          ↓
     Early Warning
```

The system classifies monitored locations into four risk levels:

| Risk Level | Meaning |
|---|---|
| 🟢 LOW | Lower current landslide risk |
| 🟡 MODERATE | Increased monitoring recommended |
| 🟠 HIGH | Elevated risk requiring attention |
| 🔴 CRITICAL | Immediate evacuation and emergency response recommended |

## ✨ Key Features

**🤖 AI-Based Risk Prediction**
Machine-learning models analyze environmental and terrain-related features to estimate landslide risk.

**🌧️ Rainfall Monitoring**
Rainfall information can be incorporated into localized landslide risk assessment.

**🌱 IoT Sensor Integration**
The platform supports environmental sensor readings such as rainfall, soil moisture, and soil temperature.

**📡 MQTT Communication**
MQTT provides lightweight communication between sensor devices, the MQTT broker, and the monitoring backend.

**🗺️ Risk Visualization**
The React dashboard displays monitored locations on a map and lists their current risk levels, with a live "last updated" indicator and a color legend.

**⚡ Real-Time Monitoring**
Incoming sensor data can be continuously processed and converted into updated risk predictions; the dashboard polls for fresh data automatically.

**🔄 IoT Sensor Simulator**
A built-in simulator generates sensor data for demonstrations when physical IoT hardware is unavailable.

**🐳 Dockerized Deployment**
The application can be deployed using Docker Compose with separate services for the backend, frontend, MQTT broker, gateway, and sensor simulator — or as a public Render deployment (see below).

**🔐 Rate Limiting & Admin Auth**
The public prediction endpoint is rate-limited per IP, and privileged endpoints (like triggering a manual data sync) require an admin API key.

## 🏗️ System Architecture

```
                  ┌──────────────────────┐
                  │     IoT Sensors      │
                  │ Rain / Soil / Temp   │
                  └──────────┬───────────┘
                             │
                             ▼
                     ┌──────────────┐
                     │ MQTT Broker  │
                     │  Mosquitto   │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ IoT Gateway  │
                     └──────┬───────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │ FastAPI Backend  │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │  ML Risk Model   │
                   └────────┬─────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │ Risk Score / Level │
                  └─────────┬──────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │  React Dashboard   │
                  └────────────────────┘
```

## 🧠 Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React.js, Vite |
| Backend | Python, FastAPI |
| Machine Learning | Python, Scikit-learn |
| Database | PostgreSQL (production) / SQLite (local dev) |
| Rate Limiting | SlowAPI |
| IoT Communication | MQTT |
| MQTT Broker | Eclipse Mosquitto |
| Containerization | Docker, Docker Compose |
| Data Processing | Pandas, NumPy |
| GIS / Geospatial | GeoPandas |
| Hosting | Render (Blueprint deploy) |

## 📁 Project Structure

```
SANRAKSHA/
│
├── backend/
│   ├── app/
│   ├── data/
│   └── requirements.txt
│
├── frontend/
│   ├── web-dashboard/
│   └── nginx.conf
│
├── iot/
│   ├── gateway/
│   └── simulator/
│
├── ml/
│
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── render.yaml
├── mosquitto.conf
└── README.md
```

## 🚀 Deploy your own copy (Render, free tier)

1. Fork or clone this repo, push it to your own GitHub.
2. On [render.com](https://render.com), click **New → Blueprint** and select your repo. Render will detect `render.yaml` and provision three services automatically:
   - `sanraksha-backend` — the FastAPI app (Docker)
   - `sanraksha-frontend` — the React dashboard (static site)
   - `sanraksha-db` — a managed Postgres database
3. Once deployed, open the frontend service's URL — that's your public dashboard.

See [`render.yaml`](./render.yaml) for the exact configuration, including environment variables and the auto-generated admin/ingest keys.

## 🐳 Run locally with Docker

**Prerequisites:** Docker Desktop, Git

```bash
git clone https://github.com/VigneshSivakumar-hen/SANRAKSHA.git
cd SANRAKSHA
docker compose up -d --build
```

Check running services:

```bash
docker compose ps
```

The local stack includes:

| Service | Role |
|---|---|
| Backend | FastAPI |
| Frontend | React + Nginx |
| MQTT Broker | Mosquitto |
| Gateway | IoT → Backend bridge |
| Simulator | Simulated sensor data |

Open the dashboard at **http://localhost**, health check at **http://localhost/health**.

## 🔄 Data Flow

```
Sensor Data
    ↓
MQTT Topic
    ↓
Mosquitto Broker
    ↓
IoT Gateway
    ↓
FastAPI API
    ↓
Feature Processing
    ↓
Machine Learning Model
    ↓
Risk Score
    ↓
Risk Classification
    ↓
React Dashboard
```

## 📊 Example Monitoring Locations

The prototype demonstrates monitoring for five locations, each with sensor data and a corresponding landslide risk score:

- Munnar, Kerala
- Wayanad, Kerala
- Nilgiris, Tamil Nadu
- Darjeeling, West Bengal
- Shimla, Himachal Pradesh

## 🛡️ Early-Warning Concept

```
Environmental Monitoring
        ↓
Risk Prediction
        ↓
Risk Classification
        ↓
Dashboard Alert
        ↓
Potential Warning / Response
```

Future versions can integrate additional warning channels such as SMS alerts, mobile notifications, local sirens, multilingual alerts, and government/emergency communication systems.

## 🌐 Future Enhancements

SANRAKSHA is designed to evolve into a larger disaster-management platform. Planned enhancements include:

- 🛰️ Satellite-based terrain and rainfall analysis
- 🗺️ Advanced GIS risk maps
- 📱 Flutter mobile application
- 🌧️ Real-time weather data integration (real IMD API, beyond the current mock data)
- 📡 LoRa / LoRaWAN sensor networks
- 📵 Offline-first monitoring and synchronization
- 🚨 SMS and emergency alerts
- 🗣️ Multilingual warning notifications
- 👥 Crowdsourced landslide reporting
- 🧠 Advanced machine-learning models
- 📈 Historical risk analytics

## 🔐 Security & Reliability

Current state:

- ✅ Admin API key required for privileged endpoints (manual data sync)
- ✅ Per-IP rate limiting on the public prediction endpoint
- ✅ Shared-secret token for IoT gateway ingestion
- ✅ Managed Postgres option for durable storage

Planned production improvements:

- Secure MQTT communication (TLS)
- Role-based access control
- Sensor validation
- Offline data buffering
- Fault-tolerant communication

## 🎯 Smart India Hackathon

- **Event:** Smart India Hackathon 2026
- **Problem Statement:** 26001
- **Domain:** Disaster Management
- **Project:** SANRAKSHA – AI-Powered Landslide Prediction & Early Warning System

## 👨‍💻 Project Status

**Current stage:** Deployed working prototype

The current prototype demonstrates:

- FastAPI backend, publicly deployed
- React monitoring dashboard, publicly deployed
- Machine-learning-based risk prediction
- PostgreSQL persistence (SQLite for local dev)
- MQTT communication (local/Docker Compose)
- IoT gateway (local/Docker Compose)
- Sensor data simulator (local/Docker Compose)
- Dockerized deployment + one-click Render Blueprint deployment

The system is being developed toward a more comprehensive AI-powered landslide monitoring and early-warning platform.

## 📌 Disclaimer

SANRAKSHA is a prototype developed for research, demonstration, and Smart India Hackathon purposes.

Risk predictions should not be treated as a replacement for official geological, meteorological, or emergency-management warnings.

## ⭐ Support

If you find the project interesting, consider giving the repository a ⭐ on GitHub.

---

**SANRAKSHA — Monitor. Predict. Warn. Protect.**
