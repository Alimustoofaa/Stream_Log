# SMARTCAM Log Viewer Dashboard

A modern, high-performance, Grafana-inspired web dashboard for streaming and analyzing Python application logs in real-time. Built with FastAPI, WebSockets, and Tailwind CSS.

## 🌟 Key Features

* **Real-time Streaming:** Uses WebSockets to continuously push new logs to the browser without polling.
* **Smart Parsing:** Automatically detects log levels (`INFO`, `WARNING`, `ERROR`) and extracts inline image paths (`.jpg`) and JSON files (`.json`).
* **Time-Series Volume Chart:** Live, animated Chart.js histogram showing the volume of new logs arriving, color-coded by severity.
* **Advanced Filtering:**
  * Quick-toggle buttons to filter by log level.
  * Fast text searching.
  * **Regex Support:** Wrap your search in forward slashes (e.g. `/timeout|disconnect/`) to perform complex regular expression filtering.
* **Interactive Viewers:**
  * **Image Modal:** Click on any log containing an image path to open an interactive modal with drag-to-pan and scroll-to-zoom capabilities.
  * **JSON File Modal:** Click on JSON log paths to view beautifully formatted, pretty-printed JSON data directly in the dashboard.
  * **Inline JSON:** Expand nested dictionary/JSON payloads right inside the log row.
* **Historical Exploration:**
  * Browse older logs via the `/history` directory view.
  * Instantly jump to a specific day using the **Calendar Date Picker** in the top navigation.
* **Export to CSV:** Download your currently filtered logs to a CSV file for external analysis with a single click.
* **UI/UX Refinements:**
  * **Light / Dark Mode:** Toggle between sleek dark and clean light themes. Saves to your browser automatically.
  * **Pause/Resume:** Freeze the live log stream to investigate fast-moving errors.
  * **Bookmarking:** Click any log row to permanently highlight it so you don't lose your place.

## 🛠️ Configuration

The application reads log files and images from your local file system. By default, it expects them in your home directory, but this can be customized using environment variables.

### Environment Variables

* `LOG_DIR`: Path to the root directory containing your log files (Default: `~/Logger/Master`)
* `IMAGE_DIR`: Path to the root directory containing your camera captures and labels (Default: `~/Camera/Captures`)

## 🚀 Running the Server

1. Ensure you have the required dependencies installed (FastAPI, Uvicorn, Jinja2).
2. Start the application using Uvicorn:

```bash
# Run with default paths
uvicorn main:app --host 0.0.0.0 --port 9000 --reload

# Or run with custom paths
LOG_DIR="/custom/logs" IMAGE_DIR="/custom/images" uvicorn main:app --host 0.0.0.0 --port 9000
```

3. Open your browser and navigate to `http://localhost:9000`.

## 📁 Directory Structure

The backend expects logs to be structured by date for historical exploration:
```text
$LOG_DIR/
├── logging.log                   <-- Current live log
└── 2026/
    └── 04/
        └── 28/
            ├── logging_01.log    <-- Historical logs
            └── logging_02.log
```
