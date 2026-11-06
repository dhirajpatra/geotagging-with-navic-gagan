import json
import sqlite3
import os

DB_PATH = "/home/pi/coffee_plantation_inspection.db"
OUTPUT_GEOJSON = "/home/pi/plantation_map.geojson"

def export_sqlite_to_geojson():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return

    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows accessing fields by name
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM tree_inspections;")
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.close()
        return
        
    conn.close()

    if not rows:
        print("No inspection records found in the database to export.")
        return

    # Initialize the GeoJSON structure
    geojson_data = {
        "type": "FeatureCollection",
        "features": []
    }

    for row in rows:
        # Construct a GeoJSON feature for each logged coffee tree
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                # GeoJSON coordinates format is strictly [longitude, latitude, elevation]
                "coordinates": [row["longitude"], row["latitude"]]
            },
            "properties": {
                "db_id": row["id"],
                "timestamp": row["timestamp"],
                "altitude_meters": row["altitude"],
                "gagan_mode": row["gagan_status"],
                "captured_frame": os.path.basename(row["image_filename"]),
                "crop_diagnostics": row["health_status"]
            }
        }
        
        # If altitude data exists, append it safely to coordinates
        if row["altitude"] is not None:
            feature["geometry"]["coordinates"].append(row["altitude"])
            
        geojson_data["features"].append(feature)

    # Save to file
    with open(OUTPUT_GEOJSON, "w") as f:
        json.dump(geojson_data, f, indent=4)

    print(f"[SUCCESS] Exported {len(rows)} nodes to mapping file: {OUTPUT_GEOJSON}")

if __name__ == "__main__":
    export_sqlite_to_geojson()
