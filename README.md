# Arduino Controller / Serial Monitor

This project was designed for a dual-axis solar tracker but can be adapted for any sensor/stepper-motor array.

## Architecture Stack

This project is separated into three distinct layers to cleanly decouple the hardware logic from the user interface.

* **Frontend (SvelteKit + Tailwind CSS + Chart.js):** Reactive web dashboard that polls the API for live data and provides manual motor override controls.
* **Backend API (Python + FastAPI + PySerial):** A lightweight gateway server. It translates HTTP REST requests from the web into raw Serial byte commands for the Arduino, and vice versa.
* **Hardware (Arduino + C++):** The physical controller handling 4x LDR light sensors and 2x Stepper Motors via a CNC shield. (Code available [here](https://github.com/tretegg/Solar-Tracker-Arduino))

## Getting Started

To run the full stack, you will need to open two separate terminal windows (one for the backend, one for the frontend) and upload a C++ script to your Arduino.

### Python Backend
Ensure you have Python installed. Navigate to your backend directory:

```bash
cd backend

# Install the required libraries
pip install fastapi uvicorn pyserial

# Start the API server
uvicorn server:app --reload
```

### Svelte Frontend
Ensure you have Node.js installed. Navigate to your ui directory:

```bash
cd ui

# Install the required libraries
npm install

# Host the site locally
npm run dev
```

Once everything is running, open your web browser and navigate to http://localhost:5173. 
The dashboard will automatically perform a handshake with the Python gateway on port 8000, and the telemetry stream will begin.

## API Endpoints

The FastAPI server provides the following endpoints (accessible at http://localhost:8000/docs):

GET /api/status: Sends "STATUS\n" over USB encoded in UTF-8.

POST /api/move: Expects a JSON {"axis": "azimuth|elevation", "direction": "forward|backward", "steps": int}. Translates this into a string format (e.g. "azimuth:clockwise:10\n") and sends it over USB encoded in UTF-8.

POST /api/change_mode: Expects a JSON {"mode": "MODE:AUTO|MODE:MANUAL"}. Translates this into a string (e.g. "MODE:AUTO\n") and sends it over USB encoded in UTF-8
