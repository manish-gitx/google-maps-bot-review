import subprocess
import time
import re
from pathlib import Path
from utils.logger import log
import config


class EmulatorManager:
    """Manages Android emulator lifecycle: create, boot, configure, destroy."""

    def __init__(self):
        self.adb = config.ADB_PATH
        self.emulator = config.EMULATOR_PATH
        self.avdmanager = config.AVD_MANAGER_PATH

    def list_avds(self) -> list[str]:
        """List all available AVDs."""
        try:
            result = subprocess.run(
                [self.emulator, "-list-avds"],
                capture_output=True, text=True, timeout=10,
            )
            avds = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
            return avds
        except Exception as e:
            log.error(f"Failed to list AVDs: {e}")
            return []

    def create_avd(self, avd_name: str, device: str = None, api_level: int = None) -> bool:
        """Create a new Android Virtual Device."""
        device = device or config.DEFAULT_DEVICE
        api_level = api_level or config.ANDROID_API_LEVEL
        system_image = f"system-images;android-{api_level};google_apis;x86_64"

        log.info(f"Creating AVD: {avd_name} (device={device}, API={api_level})")

        # Download system image if needed
        sdkmanager = str(Path(config.ANDROID_HOME) / "cmdline-tools" / "latest" / "bin" / "sdkmanager")
        try:
            subprocess.run(
                [sdkmanager, "--install", system_image],
                capture_output=True, text=True, timeout=300,
            )
        except Exception:
            log.warning("Could not auto-install system image. Ensure it's installed manually.")

        # Create the AVD
        try:
            result = subprocess.run(
                [self.avdmanager, "create", "avd",
                 "--name", avd_name,
                 "--package", system_image,
                 "--device", device,
                 "--force"],
                input="no\n",  # Don't create custom hardware profile
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                log.info(f"AVD created: {avd_name}")
                return True
            else:
                log.error(f"AVD creation failed: {result.stderr}")
                return False
        except Exception as e:
            log.error(f"AVD creation error: {e}")
            return False

    def boot_emulator(self, avd_name: str, port: int = 5554, proxy: dict | None = None,
                      wipe_data: bool = False) -> str | None:
        """Boot an emulator and return its ADB serial (e.g., 'emulator-5554').

        Returns None if boot fails.
        """
        serial = f"emulator-{port}"
        log.info(f"Booting emulator: {avd_name} on port {port}")

        cmd = [
            self.emulator,
            "-avd", avd_name,
            "-port", str(port),
            "-no-audio",
            "-no-snapshot-save",
            "-gpu", "swiftshader_indirect",
        ]

        if wipe_data:
            cmd.append("-wipe-data")

        if proxy:
            proxy_str = f"{proxy['host']}:{proxy['port']}"
            cmd.extend(["-http-proxy", proxy_str])

        try:
            # Launch emulator in background
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            log.error(f"Failed to launch emulator: {e}")
            return None

        # Wait for boot to complete
        if self._wait_for_boot(serial):
            log.info(f"Emulator booted: {serial}")
            return serial
        else:
            log.error(f"Emulator boot timed out: {serial}")
            self.kill_emulator(serial)
            return None

    def _wait_for_boot(self, serial: str, timeout: int = None) -> bool:
        """Wait for emulator to fully boot."""
        timeout = timeout or config.EMULATOR_BOOT_TIMEOUT
        start = time.time()

        # Wait for device to appear in adb
        while time.time() - start < timeout:
            try:
                result = subprocess.run(
                    [self.adb, "-s", serial, "shell", "getprop", "sys.boot_completed"],
                    capture_output=True, text=True, timeout=5,
                )
                if result.stdout.strip() == "1":
                    # Extra wait for services to stabilize
                    time.sleep(5)
                    return True
            except Exception:
                pass
            time.sleep(3)

        return False

    def kill_emulator(self, serial: str):
        """Kill a running emulator."""
        try:
            subprocess.run(
                [self.adb, "-s", serial, "emu", "kill"],
                capture_output=True, timeout=10,
            )
            log.info(f"Emulator killed: {serial}")
        except Exception as e:
            log.warning(f"Failed to kill emulator {serial}: {e}")

    def wipe_app_data(self, serial: str, package: str):
        """Clear app data for a specific package."""
        try:
            subprocess.run(
                [self.adb, "-s", serial, "shell", "pm", "clear", package],
                capture_output=True, timeout=10,
            )
            log.info(f"Cleared data for {package}")
        except Exception as e:
            log.warning(f"Failed to clear {package}: {e}")

    def remove_google_account(self, serial: str):
        """Remove all Google accounts from the device."""
        try:
            # List accounts
            result = subprocess.run(
                [self.adb, "-s", serial, "shell", "dumpsys", "account"],
                capture_output=True, text=True, timeout=10,
            )

            # Remove account via am command
            subprocess.run(
                [self.adb, "-s", serial, "shell", "pm", "clear",
                 "com.google.android.gms"],
                capture_output=True, timeout=10,
            )
            log.info("Google accounts removed")
        except Exception as e:
            log.warning(f"Failed to remove Google account: {e}")

    def take_screenshot(self, serial: str, local_path: str):
        """Take a screenshot from the emulator."""
        remote_path = "/sdcard/screenshot.png"
        try:
            subprocess.run(
                [self.adb, "-s", serial, "shell", "screencap", "-p", remote_path],
                capture_output=True, timeout=10,
            )
            subprocess.run(
                [self.adb, "-s", serial, "pull", remote_path, local_path],
                capture_output=True, timeout=10,
            )
            subprocess.run(
                [self.adb, "-s", serial, "shell", "rm", remote_path],
                capture_output=True, timeout=5,
            )
            log.info(f"Screenshot saved: {local_path}")
        except Exception as e:
            log.error(f"Screenshot failed: {e}")

    def get_running_emulators(self) -> list[str]:
        """Get list of running emulator serials."""
        try:
            result = subprocess.run(
                [self.adb, "devices"],
                capture_output=True, text=True, timeout=10,
            )
            serials = []
            for line in result.stdout.strip().split("\n")[1:]:
                if "emulator" in line and "device" in line:
                    serial = line.split("\t")[0].strip()
                    serials.append(serial)
            return serials
        except Exception:
            return []

    def install_apk(self, serial: str, apk_path: str) -> bool:
        """Install an APK on the emulator."""
        try:
            result = subprocess.run(
                [self.adb, "-s", serial, "install", "-r", "-g", apk_path],
                capture_output=True, text=True, timeout=120,
            )
            if "Success" in result.stdout:
                log.info(f"APK installed: {apk_path}")
                return True
            log.error(f"APK install failed: {result.stdout} {result.stderr}")
            return False
        except Exception as e:
            log.error(f"APK install error: {e}")
            return False

    def delete_avd(self, avd_name: str):
        """Delete an AVD."""
        try:
            subprocess.run(
                [self.avdmanager, "delete", "avd", "--name", avd_name],
                capture_output=True, timeout=30,
            )
            log.info(f"AVD deleted: {avd_name}")
        except Exception as e:
            log.warning(f"Failed to delete AVD {avd_name}: {e}")
