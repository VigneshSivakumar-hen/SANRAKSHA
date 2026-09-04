🏔️ SANRAKSHA
AI-Powered Landslide Prediction & Early Warning System

Smart India Hackathon 2026 – Problem Statement 26001

SANRAKSHA is an AI-powered landslide risk monitoring and early-warning platform designed to monitor vulnerable mountainous regions and provide timely, localized risk information.

The platform combines IoT sensor data, rainfall information, terrain-related features, historical landslide data and machine-learning-based risk prediction to estimate landslide risk for monitored locations.

🚨 Problem

Landslides in mountainous regions can cause:

Loss of life
Road blockages
Infrastructure damage
Communication disruption
Delayed emergency response

Conventional monitoring approaches may be difficult to deploy at a local level and may not provide sufficiently localized and timely risk information.

SANRAKSHA aims to provide a scalable monitoring and early-warning platform using AI, IoT, MQTT and geospatial technologies.

💡 Solution

SANRAKSHA follows a continuous monitoring pipeline:

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

The system classifies monitored locations into three risk levels:

Risk Level	Meaning
🟢 LOW	Lower current landslide risk
🟡 MODERATE	Increased monitoring recommended
🔴 HIGH	Elevated risk requiring attention
✨ Key Features
🤖 AI-Based Risk Prediction

Machine-learning models analyze environmental and terrain-related features to estimate landslide risk.

🌧️ Rainfall Monitoring

Rainfall information can be incorporated into localized landslide risk assessment.

🌱 IoT Sensor Integration

The platform supports environmental sensor readings such as:

Rainfall
Soil moisture
Soil temperature
📡 MQTT Communication

MQTT provides lightweight communication between sensor devices, the MQTT broker and the monitoring backend.

🗺️ Risk Visualization

The React dashboard displays monitored locations and their current risk levels.

⚡ Real-Time Monitoring

Incoming sensor data can be continuously processed and converted into updated risk predictions.

🔄 IoT Sensor Simulator

A built-in simulator generates sensor data for demonstrations when physical IoT hardware is unavailable.

🐳 Dockerized Deployment

The application can be deployed using Docker Compose with separate services for the backend, frontend, MQTT broker, gateway and sensor simulator.

🏗️ System Architecture
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
🧠 Technology Stack
Layer	Technology
Frontend	React.js, Vite
Backend	Python, FastAPI
Machine Learning	Python, Scikit-learn
Database	SQLite
IoT Communication	MQTT
MQTT Broker	Eclipse Mosquitto
Containerization	Docker, Docker Compose
Data Processing	Pandas, NumPy
GIS / Geospatial	GeoPandas
Visualization	Web-based dashboard
📁 Project Structure
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
├── mosquitto.conf
└── README.md
🚀 Run with Docker
Prerequisites

Install:

Docker Desktop
Git

Clone the repository:

git clone https://github.com/VigneshSivakumar-hen/SANRAKSHA.git
cd SANRAKSHA

Start the complete system:

docker compose up -d --build

Check running services:

docker compose ps

The system includes:

Backend       → FastAPI
Frontend      → React + Nginx
MQTT Broker   → Mosquitto
Gateway       → IoT → Backend bridge
Simulator     → Simulated sensor data

Open the dashboard:

http://localhost

Health check:

http://localhost/health
🔄 Data Flow
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
📊 Example Monitoring Locations

The prototype can demonstrate monitoring for locations such as:

Munnar
Wayanad
Nilgiris
Darjeeling
Shimla

Each location receives sensor data and a corresponding landslide risk score.

🛡️ Early-Warning Concept

The system is designed to support an early-warning workflow:

Environmental Monitoring
        ↓
Risk Prediction
        ↓
Risk Classification
        ↓
Dashboard Alert
        ↓
Potential Warning / Response

Future versions can integrate additional warning channels such as:

SMS alerts
Mobile notifications
Local sirens
Multilingual alerts
Government/emergency communication systems
🌐 Future Enhancements

SANRAKSHA is designed to evolve into a larger disaster-management platform.

Planned enhancements include:

🛰️ Satellite-based terrain and rainfall analysis
🗺️ Advanced GIS risk maps
📱 Flutter mobile application
🌧️ Real-time weather data integration
📡 LoRa / LoRaWAN sensor networks
📵 Offline-first monitoring and synchronization
🚨 SMS and emergency alerts
🗣️ Multilingual warning notifications
👥 Crowdsourced landslide reporting
🧠 Advanced machine-learning models
📈 Historical risk analytics
☁️ Cloud deployment and scalable infrastructure
🔐 Security & Reliability

The platform is designed with reliability and secure communication in mind.

Planned production improvements include:

API authentication
Secure MQTT communication
HTTPS
Environment-based secrets
Role-based access
Sensor validation
Offline data buffering
Fault-tolerant communication
🎯 Smart India Hackathon

Event: Smart India Hackathon 2026
Problem Statement: 26001
Domain: Disaster Management
Project: SANRAKSHA – AI-Powered Landslide Prediction & Early Warning System

👨‍💻 Project Status

Current Stage: Working prototype

The current prototype demonstrates:

FastAPI backend
React monitoring dashboard
Machine-learning-based risk prediction
SQLite persistence
MQTT communication
IoT gateway
Sensor data simulator
Dockerized deployment

The system is being developed toward a more comprehensive AI-powered landslide monitoring and early-warning platform.

📌 Disclaimer

SANRAKSHA is a prototype developed for research, demonstration and Smart India Hackathon purposes.

Risk predictions should not be treated as a replacement for official geological, meteorological or emergency-management warnings.

⭐ Support

If you find the project interesting, consider giving the repository a ⭐ on GitHub.

SANRAKSHA — Monitor. Predict. Warn. Protect.
