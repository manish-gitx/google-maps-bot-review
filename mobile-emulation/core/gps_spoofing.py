import random
import subprocess
import time
from utils.logger import log
import config


def set_gps_location(serial: str, latitude: float, longitude: float, add_noise: bool = True):
    """Set fake GPS coordinates on the emulator.

    Args:
        serial: ADB serial of the emulator (e.g., emulator-5554)
        latitude: Target latitude
        longitude: Target longitude
        add_noise: Add slight randomization (±0.001 degrees ≈ 100m)
    """
    if add_noise:
        # Add natural GPS drift (±50-200 meters)
        latitude += random.uniform(-0.002, 0.002)
        longitude += random.uniform(-0.002, 0.002)

    adb = config.ADB_PATH

    # Method 1: ADB emu geo fix (longitude first, then latitude)
    try:
        subprocess.run(
            [adb, "-s", serial, "emu", "geo", "fix", str(longitude), str(latitude)],
            capture_output=True, timeout=5,
        )
        log.info(f"GPS set to: {latitude:.6f}, {longitude:.6f}")
    except Exception as e:
        log.error(f"Failed to set GPS via emu geo fix: {e}")

    # Method 2: Also set via settings for apps that check LocationManager
    try:
        # Enable mock locations
        subprocess.run(
            [adb, "-s", serial, "shell", "settings", "put", "secure",
             "mock_location", "1"],
            capture_output=True, timeout=5,
        )
        # Allow mock location for Maps
        subprocess.run(
            [adb, "-s", serial, "shell", "appops", "set",
             config.MAPS_PACKAGE, "android:mock_location", "allow"],
            capture_output=True, timeout=5,
        )
    except Exception:
        pass


def simulate_travel(serial: str, start_lat: float, start_lon: float,
                    end_lat: float, end_lon: float, steps: int = 10, duration: float = 30.0):
    """Simulate gradual travel from one location to another.

    This prevents sudden GPS jumps that trigger location fraud detection.
    """
    log.info(f"Simulating travel: ({start_lat:.4f},{start_lon:.4f}) -> ({end_lat:.4f},{end_lon:.4f})")

    lat_step = (end_lat - start_lat) / steps
    lon_step = (end_lon - start_lon) / steps
    sleep_time = duration / steps

    for i in range(steps + 1):
        lat = start_lat + lat_step * i + random.uniform(-0.0003, 0.0003)
        lon = start_lon + lon_step * i + random.uniform(-0.0003, 0.0003)
        set_gps_location(serial, lat, lon, add_noise=False)
        time.sleep(sleep_time)

    log.info("Travel simulation complete")


# Common business location coordinates for reference
SAMPLE_LOCATIONS = {
    "new_york_manhattan": (40.7580, -73.9855),
    "los_angeles_dtla": (34.0407, -118.2468),
    "chicago_loop": (41.8819, -87.6278),
    "houston_downtown": (29.7604, -95.3698),
    "miami_beach": (25.7907, -80.1300),
    "san_francisco_soma": (37.7849, -122.4094),
    "seattle_downtown": (47.6062, -122.3321),
    "denver_downtown": (39.7392, -104.9903),
    "boston_downtown": (42.3601, -71.0589),
    "austin_downtown": (30.2672, -97.7431),
}
