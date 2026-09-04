# 🏔️ SANRAKSHA
## AI-Powered Landslide Prediction & Early Warning System

> **Smart India Hackathon 2026 – Problem Statement 26001**

SANRAKSHA is an AI-powered landslide risk monitoring and early-warning platform designed to help monitor vulnerable mountainous regions and provide timely risk information.

The system combines rainfall data, IoT sensor readings, terrain information, historical landslide data and machine-learning-based risk prediction to generate localized landslide risk levels.

---

## 🚨 Problem

Landslides in mountainous regions can cause:

- Loss of life
- Road blockages
- Infrastructure damage
- Communication disruption
- Delayed emergency response

Existing monitoring systems can be difficult to deploy at a local level and may not provide timely, localized warnings.

SANRAKSHA aims to provide a scalable monitoring and early-warning platform using AI, IoT and geospatial technologies.

---

## 💡 Solution

SANRAKSHA follows a continuous monitoring pipeline:

```text
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

The system classifies monitored locations into:

🟢 LOW
🟡 MODERATE
🔴 HIGH
✨ Key Features
🤖 AI-Based Risk Prediction

Machine-learning models analyze environmental and terrain-related features to estimate landslide risk.

🌧️ Rainfall Monitoring

Rainfall information can be incorporated into localized risk assessment.

🌱 IoT Sensor Integration

The platform supports sensor readings such as:

Rainfall
Soil moisture
Soil temperature
📡 MQTT Communication

MQTT provides lightweight communication between sensor devices and the monitoring backend.

🗺️ Risk Visualization

The web dashboard displays monitored locations and their current risk levels.

⚡ Real-Time Monitoring

Sensor data can be continuously processed and converted into updated risk predictions.

🔄 IoT Simulator

A built-in simulator generates sensor data for demonstrations when physical hardware is unavailable.

🐳 Dockerized Deployment

The complete application can be launched using Docker Compose.

🏗️ System Architecture
                  ┌──────────────────────┐
                  │   IoT Sensors        │
                  │ Rain / Soil / Temp   │
                  └──────────┬───────────┘
                             │
                             ▼
                     ┌──────────────┐
                     │ MQTT Broker  │
                     │ Mosquitto    │
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
                   │ ML Risk Model    │
                   └────────┬─────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │ Risk Score/Level   │
                  └─────────┬──────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │ React Dashboard    │
                  └────────────────────┘
