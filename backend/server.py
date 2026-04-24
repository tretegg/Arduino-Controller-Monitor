from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import random
import json
import serial

# Run the server with:
# uvicorn server:app --reload

app = FastAPI()

# Enable CORS so our Svelte frontend can talk to this API without security issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        # Generate some fluctuating dummy data
        fake_data = {
            "ldr_top_left": random.randint(400, 600),
            "ldr_top_right": random.randint(400, 600),
            "ldr_bottom_left": random.randint(400, 600),
            "ldr_bottom_right": random.randint(400, 600),
        }

        # Encode it into raw bytes, same as how it arrives over USB from an Arduino
        json_str = json.dumps(fake_data) + "\n"
        return json_str.encode('utf-8')

    def write(self, data_bytes):
        # Decode the bytes sent from the API and "move" the fake motors
        command = data_bytes.decode('utf-8').strip()
        print(f"[ARDUINO RECEIVED]: {command}")

USE_REAL_HARDWARE = False

if USE_REAL_HARDWARE:
    # Swap "COM3" with actual port later
    arduino = serial.Serial("COM3", 9600, timeout=1) 
else:
    arduino = MockSerial("MOCK_PORT", 9600)

# Define the structure of a movement command from the frontend
class MoveCommand(BaseModel):
    axis: str      # Azimuth or Elevation
    direction: str # clockwise or counterclockwise
    steps: int

# Define the structure of a mode change command
class ModeCommand(BaseModel):
    mode: str # MODE:MANUAL or MODE:AUTO

# @ is a decorator that tells FastAPI to treat this function as an endpoint for GET requests at the path /api/status
@app.get("/api/status")
def get_status():
    try:
        # Ask the Arduino for the latest data
        arduino.write("STATUS\n".encode('utf-8')) # Convert string to bytes and send to Arduino
        
        # Read the reply from the arduino
        raw_bytes = arduino.readline()
        # .strip() removes any extra whitespace or newline characters from the ends of the string
        data_string = raw_bytes.decode('utf-8').strip()
        
        # Turn it into a dictionary for the Svelte frontend
        return json.loads(data_string)
    except Exception as e:
        return {"error": "Failed to read hardware", "details": str(e)}
    
# Similar to the above, but for POST requests
@app.post("/api/move")
def move_motors(command: MoveCommand):
    # This will send a string like "Azimuth:clockwise:10" or "Elevation:counterclockwise:5" to the serial port
    instruction = f"{command.axis}:{command.direction}:{command.steps}\n"

    print(f"Sending command: {instruction}")  # Log the command for debugging
    arduino.write(instruction.encode('utf-8'))  # Convert string to bytes and send to Arduino

    return {"status": "success","message": f"Command sent: {command.axis} {command.direction} {command.steps}"}

@app.post("/api/change_mode")
def change_mode(command: ModeCommand):
    # This will send a string like "MODE:MANUAL" or "MODE:AUTO" to the serial port
    mode = f"{command.mode}\n"

    print(f"Changing mode to: {mode}") # Log the mode change for debugging
    arduino.write(mode.encode('utf-8')) # Convert string to bytes and send to Arduino

    return {"status": "success", "message": f"Mode changed to: {mode}"}