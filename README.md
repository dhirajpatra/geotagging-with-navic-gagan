# Autonomous Coffee Plantation Geo-Tagging & Diagnostics Robot

An edge-computing robotic payload system built for Raspberry Pi. It detects coffee plantation tree assets using proximity hardware, automatically logs sub-meter geo-coordinates using India's **GAGAN (GPS Aided GEO Augmented Navigation)** satellite framework, and runs hybrid diagnostic analytics (Cloud Gemini API / Local OpenCV fallback) to audit crop health.

---

## 🚀 Key System Features

* **High-Accuracy GAGAN Mapping:** Automatically parses NMEA streams from GNSS modules to track active Satellite-Based Augmentation System (SBAS) corrections.
* **Proximity-Driven Capture:** Leverages a hardware interrupt structure via `gpiod` to trigger camera captures instantly when passing tree infrastructure.
* **Hybrid Diagnostic Layer:** Taps into multimodal cloud AI (`gemini-2.5-flash`) for structural agronomy analysis, dropping down to local OpenCV HSV segmentation if internet connectivity drops out in dense fields.
* **Relational Field Database:** Archives assets directly into an optimized local SQLite engine, structured cleanly for rapid conversion into standard GIS files.

---

## 🛠️ Hardware Requirements & Wiring Map

### 1. Main Compute Payload
* **Raspberry Pi** (Pi 4 or Pi 5 recommended) running Raspberry Pi OS.
* **Camera Module:** Standard USB Web Camera or Raspberry Pi CSI Native Camera.
* **GNSS Module:** An SBAS/GAGAN capable GPS receiver (e.g., u-blox NEO-M8N or ZED-F9P) plugged via USB (`/dev/ttyUSB0`) or UART Serial.

### 2. Proximity Sensor Map (Digital IR Sensor / Ultrasonic Pinout)
Connect your Infrared Sensor to the Raspberry Pi GPIO headers following this structure:

| Sensor Pin | Raspberry Pi Pin Name | Physical Pin Number |
| :--- | :--- | :--- |
| **VCC** | 5V Power / 3.3V Power | Pin 2 / Pin 1 |
| **GND** | Ground | Pin 6 |
| **OUT (Signal)**| GPIO 17 | Pin 11 |

Here is the complete setup to make your robot fully autonomous. We will use a GPIO Infrared (IR) distance sensor to detect when the robot is parked in front of a coffee tree. Once detected, the script will instantly trigger the camera, parse GAGAN coordinates, query Gemini/OpenCV, and log the data.
We will also configure it as a Systemd Background Service so the script boots up automatically the moment you power on the Raspberry Pi in the field.

1. Hardware Wiring (IR Sensor to Pi)

Connect a standard digital IR obstacle avoidance sensor (or ultrasonic sensor) to your Raspberry Pi GPIO pins:
• VCC ➡️ Raspberry Pi 5V or 3.3V (Pin 2 or Pin 1)
• GND ➡️ Raspberry Pi GND (Pin 6)
• OUT (Signal) ➡️ Raspberry Pi GPIO 17 (Pin 11)

2. robot_inspector.py 

3. Setting Up the Field Autostart Service (Systemd)

To make sure this script fires up cleanly every time the robot gets a fresh battery pack out in the field, we will turn it into a system background daemon.

1. Create the service unit profile:

Open a terminal on your Pi and execute:bash
sudo nano /etc/systemd/system/coffeebot.service
Use code with caution.

2. Paste the following configuration blocks inside:

(Make sure to update YOUR_GEMINI_API_KEY with your actual key so the environment variable maps directly into the background runner).ini

[Unit]
Description=Autonomous Coffee Field Plant Geotagging & Vision System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
Environment="GEMINI_API_KEY=YOUR_GEMINI_API_KEY"
ExecStart=/usr/bin/python3 /home/pi/robot_inspector.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
Use code with caution.
Press Ctrl+O then Enter to save, and Ctrl+X to exit.

3. Enable and activate the deployment service:

Run these final control lines to register your agritech software suite into the Pi's master boot sequencer:bash
sudo systemctl daemon-reload
sudo systemctl enable coffeebot.service
sudo systemctl start coffeebot.service

`Use code with caution.`
Now, your robot can function completely headless out in the plantation. The moment the robot rolls past a tree, the physical proximity sensor triggers, coordinates lock using GAGAN satellite infrastructure, and the plant health diagnosis registers securely into SQLite.

---

## 📦 Software Setup & Installation

Execute this dependency setup line inside your Raspberry Pi terminal interface:

```bash
pip install opencv-python-headless google-genai pynmea2 pyserial pillow gpiod
```

---

## 🛠️ Automated Boot Deployment (Systemd Background Daemon)

To enable headless operations where the software launches autonomously upon field power-up, set up a Systemd background process configuration:

1. **Generate the unit profile file:**
   ```bash
   sudo nano /etc/systemd/system/coffeebot.service
   ```

2. **Populate the profile template:** Paste the following config lines inside, making sure to define your unique Google AI Studio key:
   ```ini
   [Unit]
   Description=Autonomous Coffee Field Plant Geotagging & Vision System
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi
   Environment="GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE"
   ExecStart=/usr/bin/python3 /home/pi/robot_inspector.py
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

3. **Register and fire up the system daemon:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable coffeebot.service
   sudo systemctl start coffeebot.service
   ```

---

## 📊 Accessing and Mapping Your Field Data

All target logs write onto the local storage database instance located at `/home/pi/coffee_plantation_inspection.db`.

* **To query the asset data logs inside the terminal:**
  ```bash
  sqlite3 /home/pi/coffee_plantation_inspection.db "SELECT timestamp, latitude, longitude, gagan_status, health_status FROM tree_inspections;"
  ```

* **To export data into a standard GIS-Ready CSV spreadsheet (for QGIS, ArcGIS, or Excel mapping):**
  ```bash
  sqlite3 -header -csv /home/pi/coffee_plantation_inspection.db "SELECT * FROM tree_inspections;" > /home/pi/plantation_report.csv
  ```

* **How to View Your Data on Google Maps & QGIS:**

Once the plantation_map.geojson file is generated, you can visually track your coordinates using these free platforms:

* Google My Maps (Easiest): Go to google.com, create a new map, and click Import. Drag and drop your .geojson file. Every coffee tree will appear as a precise pin, and clicking a pin will reveal its diagnostic health report and timestamp details.
* QGIS (Professional Agriculture Mapping): Open QGIS, go to Layer > Add Layer > Add Vector Layer, and select your .geojson file. You can style the tree points instantly by setting their color based on the crop_diagnostics field (e.g., green for healthy, red for anomalies).

## Contribute

If you want to add more features and testing with this starting point. Kindly fork my repository and can change and add your features. Also will request if possible can make your changes a pull request with this repository for others to share. Thank you.