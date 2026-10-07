import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webview
import base64
from pathlib import Path

from scripts.backup_db import create_backup 

# Prevent duplicate concurrent launches with a lockfile
LOCK_FILE = Path("/tmp/ledgerly_app.lock")

# Resolve base path correctly whether running source or PyInstaller binary
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

# Ensure this points to the actual location of assets relative to desktop_app.py
ICON_PATH = BASE_DIR / "assets" / "icon.png"

APP_TITLE = "Ledgerly ETL 2.0"
STREAMLIT_URL = "http://127.0.0.1:8501"
VLLM_URL = "http://127.0.0.1:8000/v1/models"


def get_splash_html(icon_path: Path = None) -> str:
    img_tag = '<div class="logo">📊</div>'
    
    if icon_path and icon_path.exists():
        with open(icon_path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode("utf-8")
        img_tag = f'<img class="logo-img" src="data:image/png;base64,{b64_str}" alt="Ledgerly" />'

    return f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            background-color: #0e1117;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            user-select: none;
        }}

        .logo-img {{
            width: 64px;
            height: 64px;
            object-fit: contain;
            margin-bottom: 12px;
        }}

        .logo {{
            font-size: 42px;
            margin-bottom: 10px;
        }}

        .title {{
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 25px;
            letter-spacing: 0.5px;
        }}

        .spinner {{
            border: 4px solid rgba(255, 255, 255, 0.1);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border-left-color: #3b82f6;
            animation: spin 1s linear infinite;
            margin-bottom: 25px;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .status {{
            font-size: 14px;
            color: #9ca3af;
            text-align: center;
            max-width: 80%;
            line-height: 1.5;
        }}
    </style>
</head>

<body>
    {img_tag}
    <div class="title">Ledgerly ETL 2.0</div>
    <div class="spinner"></div>
    <div id="status" class="status">
        Initializing desktop launcher...
    </div>

    <script>
        function setStatus(text) {{
            document.getElementById('status').innerText = text;
        }}
    </script>
</body>
</html>"""


def get_closing_html(icon_path: Path = None) -> str:
    img_tag = '<div class="logo">📊</div>'
    
    if icon_path and icon_path.exists():
        with open(icon_path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode("utf-8")
        img_tag = f'<img class="logo-img" src="data:image/png;base64,{b64_str}" alt="Ledgerly" />'

    return f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            background-color: #0e1117;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            user-select: none;
        }}

        .logo-img {{
            width: 64px;
            height: 64px;
            object-fit: contain;
            margin-bottom: 12px;
        }}

        .logo {{
            font-size: 42px;
            margin-bottom: 10px;
        }}

        .title {{
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 25px;
            letter-spacing: 0.5px;
        }}

        .spinner {{
            border: 4px solid rgba(255, 255, 255, 0.1);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border-left-color: #ef4444;
            animation: spin 1s linear infinite;
            margin-bottom: 25px;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .status {{
            font-size: 14px;
            color: #9ca3af;
            text-align: center;
            max-width: 80%;
            line-height: 1.5;
        }}
    </style>
</head>

<body>
    {img_tag}
    <div class="title">Stopping Ledgerly Services...</div>
    <div class="spinner"></div>
    <div class="status">
        Saving database backup and stopping containers...
    </div>
</body>
</html>"""


def detect_compose_cmd():
    """Detect available compose CLI tool."""

    if shutil.which("podman"):
        res = subprocess.run(
            ["podman", "compose", "version"],
            capture_output=True
        )

        if res.returncode == 0:
            return ["podman", "compose"]

    if shutil.which("podman-compose"):
        return ["podman-compose"]

    if shutil.which("docker"):
        res = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True
        )

        if res.returncode == 0:
            return ["docker", "compose"]

    return None


def ensure_env():
    """Ensure .env exists."""

    if not os.path.exists(".env") and os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")


def is_service_ready(url, timeout=1):
    """Check if a HTTP service is responsive."""

    try:
        req = urllib.request.urlopen(url, timeout=timeout)
        return req.getcode() == 200

    except Exception:
        return False


def update_splash_status(window, text):
    """Update status message on the loading splash screen."""

    print(f"--> {text}")

    try:
        safe_text = json.dumps(text)
        window.evaluate_js(f"setStatus({safe_text});")

    except Exception:
        # Window may already be closing.
        pass


def run_backup():
    """Run DB backup while PostgreSQL container is active."""

    print("💾 Backing up database before shutdown...")

    try:
        # Dynamically add the scripts folder to Python's path so we can import it
        script_dir = os.path.abspath("scripts")
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        
        # Call the backup function
        create_backup()
        
        print("✅ Database backup completed successfully.")

    except ImportError:
        print("⚠️ Backup script not found, skipping...")
    except Exception as e:
        print(f"⚠️ Backup failed: {e}")


def stop_stack(compose_cmd):
    """Backup database and shut down containers."""

    print("\n🛑 Starting application shutdown...")

    # 1. Backup database while PostgreSQL is still running
    run_backup()

    # 2. Shut down containers
    print(
        f"🧹 Shutting down containers via "
        f"{' '.join(compose_cmd)}..."
    )

    try:
        subprocess.run(
            compose_cmd + ["down"],
            timeout=15,
            check=False
        )

    except subprocess.TimeoutExpired:
        print("⚠️ Warning: Container shutdown timed out.")

    except Exception as e:
        print(f"❌ Error stopping stack: {e}")

    print("👋 Ledgerly successfully stopped.")


def stop_stack_and_destroy(window, compose_cmd, shutdown_event):
    """Run container teardown in background thread, then signal window close."""
    print("🛑 Signaling boot sequence to abort...")
    shutdown_event.set()

    try:
        stop_stack(compose_cmd)
    except Exception as e:
        print(f"❌ Error during stop_stack: {e}")
    finally:
        # Guarantee lockfile cleanup
        if LOCK_FILE.exists():
            try:
                LOCK_FILE.unlink()
            except Exception:
                pass
        
        print("⚡ Destroying PyWebView window now...")
        # Schedule window destruction safely back on PyWebView thread
        try:
            window.destroy()
        except Exception as e:
            print(f"⚠️ Window destroy error (may already be closed): {e}")


# Track whether cleanup has already been initiated to avoid infinite loop
CLEANUP_STARTED = False

def on_closing(window, compose_cmd, shutdown_event):
    """
    Handler for window closing event.
    """
    global CLEANUP_STARTED

    # If cleanup is already running, allow the window to close on second click
    if CLEANUP_STARTED:
        print("⚠️ Force closing window...")
        if LOCK_FILE.exists():
            try:
                LOCK_FILE.unlink()
            except Exception:
                pass
        return True

    CLEANUP_STARTED = True
    print("\n🪟 Window closing requested...")

    # Render closing overlay
    try:
        window.load_html(get_closing_html(ICON_PATH))
    except Exception as e:
        print(f"Failed to display closing screen: {e}")

    # Launch teardown thread
    cleanup_thread = threading.Thread(
        target=stop_stack_and_destroy,
        args=(window, compose_cmd, shutdown_event),
        daemon=True,
        name="cleanup-thread"
    )
    cleanup_thread.start()

    # Block initial close so overlay shows while cleanup runs
    return False

def boot_sequence(window, compose_cmd, shutdown_event):
    """Background startup sequence."""

    try:
        ensure_env()

        # ------------------------------------------------------------
        # 1. Check vLLM Server
        # ------------------------------------------------------------

        update_splash_status(
            window,
            "Checking local vLLM AI server status..."
        )

        if shutdown_event.is_set():
            print("🛑 Shutdown requested before vLLM startup.")
            return

        if not is_service_ready(VLLM_URL):

            vllm_script = os.path.abspath("./scripts/vllm_start.sh")

            if os.path.exists(vllm_script):

                update_splash_status(
                    window,
                    "Starting local vLLM AI server..."
                )

                if shutdown_event.is_set():
                    return

                subprocess.run(
                    [vllm_script],
                    check=True
                )

            else:

                update_splash_status(
                    window,
                    "vLLM start script not found, skipping..."
                )

        # ------------------------------------------------------------
        # 2. Start containers
        # ------------------------------------------------------------

        if shutdown_event.is_set():
            print("🛑 Shutdown requested before container startup.")
            return

        update_splash_status(
            window,
            f"Spinning up containers "
            f"({' '.join(compose_cmd)})..."
        )

        subprocess.run(
            [*compose_cmd, "up", "-d", "--build"],
            check=True
        )

        if shutdown_event.is_set():
            print("🛑 Shutdown requested after container startup.")
            return

        # ------------------------------------------------------------
        # 3. Wait for Streamlit
        # ------------------------------------------------------------

        update_splash_status(
            window,
            "Waiting for Streamlit dashboard to respond..."
        )

        max_retries = 30

        for i in range(max_retries):

            if shutdown_event.is_set():
                print("🛑 Shutdown requested while waiting for Streamlit.")
                return

            if is_service_ready(STREAMLIT_URL):

                if shutdown_event.is_set():
                    return

                update_splash_status(
                    window,
                    "Loading dashboard..."
                )

                time.sleep(0.5)

                if shutdown_event.is_set():
                    return

                window.load_url(STREAMLIT_URL)

                print("✅ Streamlit dashboard loaded.")
                return

            time.sleep(1)

        if not shutdown_event.is_set():
            update_splash_status(
                window,
                "Error: Streamlit failed to launch in time."
            )

    except Exception as e:

        if not shutdown_event.is_set():
            update_splash_status(
                window,
                f"Error starting stack: {str(e)}"
            )

            print(f"❌ Boot sequence failed: {e}")


def main():

    # ------------------------------------------------------------
    # Prevent concurrent duplicate launches
    # ------------------------------------------------------------

    if LOCK_FILE.exists():
        print("⚡ Ledgerly is already running or shutting down. Please wait...")
        sys.exit(1)

    LOCK_FILE.touch()

    try:
        # ------------------------------------------------------------
        # Detect compose
        # ------------------------------------------------------------

        compose_cmd = detect_compose_cmd()

        if not compose_cmd:
            print(
                "❌ Error: Neither Podman Compose "
                "nor Docker Compose was found."
            )
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
            sys.exit(1)

        print(
            f"✅ Using compose command: {' '.join(compose_cmd)}"
        )

        # ------------------------------------------------------------
        # Shutdown event
        # ------------------------------------------------------------

        shutdown_event = threading.Event()

        # ------------------------------------------------------------
        # Create window
        # ------------------------------------------------------------

        window = webview.create_window(
            APP_TITLE,
            html=get_splash_html(ICON_PATH),
            width=1400,
            height=900,
            resizable=True,
            min_size=(1024, 728),
        )

        def handle_closing():
            return on_closing(window, compose_cmd, shutdown_event)

        window.events.closing += handle_closing

        # ------------------------------------------------------------
        # Start boot thread
        # ------------------------------------------------------------

        boot_thread = threading.Thread(
            target=boot_sequence,
            args=(window, compose_cmd, shutdown_event),
            daemon=False,
            name="boot-sequence"
        )
        boot_thread.start()

        # ------------------------------------------------------------
        # Start pywebview
        # ------------------------------------------------------------

        print("🚀 Starting pywebview...")
        webview.start(
            icon=str(ICON_PATH) if ICON_PATH.exists() else None,
        )

        # ------------------------------------------------------------
        # WINDOW IS NOW CLOSED
        # ------------------------------------------------------------

        print("🪟 PyWebView has exited.")

        shutdown_event.set()

        print("⏳ Waiting for startup thread to finish...")
        boot_thread.join()
        print("✅ Startup thread stopped.")

        print("✅ Application shutdown complete.")

    finally:
        # Guarantee lock file is released on exit
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()

if __name__ == "__main__":
    main()