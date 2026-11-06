import os
import cv2
import time
import sqlite3
import serial
import pynmea2
from datetime import datetime
from PIL import Image
from google import genai
from google.genai import errors
import gpiod

# --- System Configurations ---
DB_NAME = "/home/pi/coffee_plantation_inspection.db" 
SERIAL_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600
IR_PIN = 17  
DEBOUNCE_COOLDOWN = 5  

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tree_inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            altitude REAL,
            gagan_status TEXT,
            image_filename TEXT,
            health_status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_gagan_coordinates():
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5) as ser:
            line = ser.readline().decode('ascii', errors='replace')
            if line.startswith('$GNGGA') or line.startswith('$GPGGA'):
                msg = pynmea2.parse(line)
                if msg.gps_qual >= 1:
                    status = "GAGAN Enhanced" if msg.gps_qual == 2 else "Standard GPS"
                    return {'lat': msg.latitude, 'lon': msg.longitude, 'alt': msg.altitude, 'status': status}
    except Exception:
        pass
    return None

def local_opencv_analysis(image_path):
    img = cv2.imread(image_path)
    if img is None: return "Analysis Failed"
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (15, 40, 40), (35, 255, 255))
    anomaly_ratio = (cv2.countNonZero(mask) / (img.shape[0] * img.shape[1])) * 100
    return f"Offline Flag: High Discoloration ({anomaly_ratio:.1f}%)" if anomaly_ratio > 5.0 else "Offline Check: Normal Green Canopy"

def cloud_gemini_analysis(image_path):
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        return local_opencv_analysis(image_path)
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        pil_image = Image.open(image_path)
        prompt = "Analyze this coffee plant image. Identify any diseases like Coffee Leaf Rust, pest damage, or check cherry ripeness. Provide a brief, single-sentence summary."
        response = client.models.generate_content(model='gemini-2.5-flash', contents=[pil_image, prompt])
        return response.text.strip()
    except Exception:
        return local_opencv_analysis(image_path)

def run_robotic_inspection_cycle():
    print("\n[+] Tree detected! Initiating inspection cycle...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[-] Error: Camera offline.")
        return
    time.sleep(0.5)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("[-] Error: Image capture failed.")
        return

    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"/home/pi/coffee_node_{timestamp_str}.jpg"
    cv2.imwrite(filename, frame)
    
    print("[+] Fetching GAGAN spatial tags...")
    coords = None
    while coords is None:
        coords = get_gagan_coordinates()
        time.sleep(0.1)
        
    print("[+] Processing vision diagnostic payload...")
    health_label = cloud_gemini_analysis(filename)
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        db_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO tree_inspections (timestamp, latitude, longitude, altitude, gagan_status, image_filename, health_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (db_time, coords['lat'], coords['lon'], coords['alt'], coords['status'], filename, health_label))
        conn.commit()
        print(f"[SUCCESS] Target logged at Lat: {coords['lat']:.6f} | Fix: {coords['status']}")
    except sqlite3.Error as e:
        print(f"[-] DB Error: {e}")
    finally:
        conn.close()

def main():
    init_database()
    print("[SYSTEM] Robot hardware interface monitoring armed...")
    
    chip = gpiod.Chip('gpiochip4') 
    line = chip.get_line(IR_PIN)
    line.request(consumer="CoffeeBot", type=gpiod.LINE_REQ_DIR_IN)
    
    last_trigger_time = 0
    
    try:
        while True:
            ir_val = line.get_value()
            current_time = time.time()
            
            if ir_val == 0 and (current_time - last_trigger_time > DEBOUNCE_COOLDOWN):
                run_robotic_inspection_cycle()
                last_trigger_time = time.time()
                
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        line.release()

if __name__ == "__main__":
    main()
