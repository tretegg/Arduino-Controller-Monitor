from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import random
import json
import serial

# uvicorn server:app --reload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, you'd lock this down to just your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This is our test hardware state
current_state = {
    "ldr_top_left": 450,
    "ldr_top_right": 460,
    "ldr_bottom_left": 470,
    "ldr_bottom_right": 480
}

class MockSerial:
    # Generates fake data.
    def __init__(self, port, baudrate):
        print(f"\nStarted Mock Serial Port on {port} at {baudrate} baud.\n")

    def readline(self):
        # Generate some fluctuating dummy data so the Svelte chart moves!
        fake_telemetry = {
            "ldr_top_left": random.randint(400, 600),
            "ldr_top_right": random.randint(400, 600),
            "ldr_bottom_left": random.randint(400, 600),
            "ldr_bottom_right": random.randint(400, 600),
        }
        # Encode it into raw bytes, exactly how it arrives over USB from an Arduino
        json_str = json.dumps(fake_telemetry) + "\n"
        return json_str.encode('utf-8')

    def write(self, data_bytes):
        # Decode the bytes sent from the API and "move" our fake motors
        command = data_bytes.decode('utf-8').strip()
        print(f"[ARDUINO RECEIVED]: {command}")
        # Do something with the command, like parse it and move the motors

USE_REAL_HARDWARE = False

if USE_REAL_HARDWARE:
    # Swap "COM3" with actual port later
    arduino = serial.Serial("COM3", 9600, timeout=1) 
else:
    arduino = MockSerial("MOCK_PORT", 9600)

# Define the structure of a movement command from the frontend
class MoveCommand(BaseModel):
    axis: str      # Azimuth or Elevation
    direction: str # forward or backward (clockwise or counterclockwise)
    steps: int

# @ is a decorator that tells FastAPI to treat this function as an endpoint for GET requests at the path /api/status
@app.get("/api/status")
def get_status():
    try:
        # Read the raw bytes and decode them into a string
        raw_bytes = arduino.readline()
        data_string = raw_bytes.decode('utf-8').strip()
        
        # Turn the string back into a Python dictionary and send to Svelte
        return json.loads(data_string)
    except Exception as e:
        return {"error": "Failed to read hardware", "details": str(e)}

# Similar to the above, but for POST requests
@app.post("/api/move")
def move_motors(command: MoveCommand):
    # This will send a string like "Azimuth:10" or "Elevation:-5" to the serial port
    instruction = f"Sending command: {command.axis}:{command.direction}:{command.steps}"

    print(instruction)  # Log the command for debugging
    arduino.write(instruction.encode('utf-8'))  # Convert string to bytes and send to Arduino

    return {"status": "success","message": f"Command sent: {command.axis} {command.direction} {command.steps}"}