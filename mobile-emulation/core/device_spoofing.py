import random
import string
import subprocess
from utils.logger import log
import config

# Real device models with matching build fingerprints
DEVICE_PROFILES = [
    {
        "model": "Pixel 7",
        "manufacturer": "Google",
        "brand": "google",
        "device": "panther",
        "product": "panther",
        "board": "pantah",
        "hardware": "tensor",
        "fingerprint": "google/panther/panther:14/AP2A.240805.005/12025142:user/release-keys",
    },
    {
        "model": "Pixel 8",
        "manufacturer": "Google",
        "brand": "google",
        "device": "shiba",
        "product": "shiba",
        "board": "shiba",
        "hardware": "tensor",
        "fingerprint": "google/shiba/shiba:14/AP2A.240805.005/12025142:user/release-keys",
    },
    {
        "model": "SM-S918B",
        "manufacturer": "samsung",
        "brand": "samsung",
        "device": "dm3q",
        "product": "dm3qxxx",
        "board": "kalama",
        "hardware": "qcom",
        "fingerprint": "samsung/dm3qxxx/dm3q:14/UP1A.231005.007/S918BXXS5CXF3:user/release-keys",
    },
    {
        "model": "SM-A546B",
        "manufacturer": "samsung",
        "brand": "samsung",
        "device": "a54x",
        "product": "a54xns",
        "board": "s5e8835",
        "hardware": "exynos",
        "fingerprint": "samsung/a54xns/a54x:14/UP1A.231005.007/A546BXXS7CXE4:user/release-keys",
    },
    {
        "model": "CPH2585",
        "manufacturer": "OnePlus",
        "brand": "OnePlus",
        "device": "OP5958L1",
        "product": "OP5958L1",
        "board": "kalama",
        "hardware": "qcom",
        "fingerprint": "OnePlus/CPH2585/OP5958L1:14/UP1A.231005.007/S.1172e3d-2a6fa:user/release-keys",
    },
]


def generate_imei() -> str:
    """Generate a valid IMEI with correct Luhn check digit."""
    # TAC (Type Allocation Code) - use known real prefixes
    tac_prefixes = [
        "35391110",  # Google Pixel
        "35260911",  # Samsung
        "86388003",  # OnePlus
        "35332510",  # Google
        "35924011",  # Samsung
    ]
    tac = random.choice(tac_prefixes)
    serial = "".join([str(random.randint(0, 9)) for _ in range(6)])
    partial = tac + serial

    # Calculate Luhn check digit
    digits = [int(d) for d in partial]
    checksum = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    check_digit = (10 - (checksum % 10)) % 10

    return partial + str(check_digit)


def generate_android_id() -> str:
    """Generate a random 16-character hex Android ID."""
    return "".join(random.choices("0123456789abcdef", k=16))


def generate_mac_address() -> str:
    """Generate a random MAC address with a valid OUI prefix."""
    # Real OUI prefixes from device manufacturers
    oui_prefixes = [
        "3C:5A:B4",  # Google
        "DC:A6:32",  # Samsung
        "98:0D:51",  # OnePlus
        "F8:E4:E3",  # Google
        "A4:77:33",  # Samsung
    ]
    oui = random.choice(oui_prefixes)
    nic = ":".join([f"{random.randint(0, 255):02X}" for _ in range(3)])
    return f"{oui}:{nic}"


def generate_serial() -> str:
    """Generate a random device serial number."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=12))


def get_random_profile() -> dict:
    """Get a complete random device identity profile."""
    device = random.choice(DEVICE_PROFILES)
    return {
        **device,
        "imei": generate_imei(),
        "android_id": generate_android_id(),
        "mac_address": generate_mac_address(),
        "serial": generate_serial(),
    }


def apply_device_props(serial: str, profile: dict):
    """Apply spoofed device properties to a running emulator via adb shell."""
    adb = config.ADB_PATH
    props = {
        "ro.product.model": profile["model"],
        "ro.product.manufacturer": profile["manufacturer"],
        "ro.product.brand": profile["brand"],
        "ro.product.device": profile["device"],
        "ro.product.name": profile["product"],
        "ro.product.board": profile["board"],
        "ro.hardware": profile["hardware"],
        "ro.build.fingerprint": profile["fingerprint"],
        "ro.serialno": profile["serial"],
        "ro.boot.serialno": profile["serial"],
        "persist.sys.wifi.mac": profile["mac_address"],
    }

    log.info(f"Applying device profile: {profile['model']} (IMEI: {profile['imei']})")

    for prop, value in props.items():
        try:
            subprocess.run(
                [adb, "-s", serial, "shell", "setprop", prop, value],
                capture_output=True, timeout=5,
            )
        except Exception as e:
            log.warning(f"Failed to set {prop}: {e}")

    # Set IMEI (requires root or Magisk)
    try:
        subprocess.run(
            [adb, "-s", serial, "shell", "service", "call", "iphonesubinfo", "1",
             "s16", profile["imei"]],
            capture_output=True, timeout=5,
        )
    except Exception:
        log.warning("Could not set IMEI (may need root/Magisk)")

    # Set Android ID via settings
    try:
        subprocess.run(
            [adb, "-s", serial, "shell", "settings", "put", "secure",
             "android_id", profile["android_id"]],
            capture_output=True, timeout=5,
        )
    except Exception:
        log.warning("Could not set Android ID")

    log.info("Device properties applied")
