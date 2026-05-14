# EyeClass - Intelligent Classroom & Endpoint Monitoring System

EyeClass is a specialized, AI-powered monitoring solution designed to provide educators and administrators with real-time visibility into both student engagement and endpoint hardware health. By combining endpoint telemetry with an intelligent management dashboard, EyeClass creates a seamless teaching environment.

## Technical Implementation
This project implements a full-stack approach, split into a centralized dashboard and remote endpoint clients:
* **Backend:** Powered by **Python 3.11**, utilizing **Flask** for the web server, session management, and API layer.
* **Frontend:** A responsive, mobile-first dashboard built with Vanilla JS, CSS3, and **Chart.js** for real-time data visualization.
* **AI Integration:** Natively integrates with **Google Gemini (1.5 Flash)** to analyze classroom data and serve as an active teaching assistant.

## Core Features
* **Live Classroom Heatmap:** Real-time visual mapping of student attention and engagement levels (supporting both 'Group' and 'Single Focus' modes).
* **AI-Driven Insights:** Automatically generates actionable teaching suggestions (e.g., "Front row needs attention") based on live metrics, alongside a built-in AI chat assistant.
* **Monthly Analytics:** Comprehensive reporting system featuring radar, bar, and line charts to track long-term attendance, energy levels, and engagement trends.
* **Endpoint Telemetry:** Instant visibility into node status, allowing hardware tracking alongside educational metrics.
* **Smart Mocking/Fallback:** Built-in API key rotation and fallback responses ensure the dashboard remains functional during live demonstrations even if API limits are reached.

## Setup and Installation

### Requirements
* **Python Version:** Python 3.11 is explicitly required.
* **API Key:** A valid Google Gemini API key is required for AI features.
* **Note:** Do not modify the `requirements.txt` file to ensure environment stability.

### Installation Steps
1. Clone the repository:
   ```bash
   git clone [https://github.com/Adir23/EyeClass.git](https://github.com/Adir23/EyeClass.git)

2. Upgrade pip:
    python -m pip install --upgrade pip

3. Install dependencies:
    pip install -r requirements.txt

Developed by Itay Parienty and Adir Berger.