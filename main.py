import os
import glob
from pathlib import Path
from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
import urllib.parse

import uvicorn
import asyncio
import collections
import json
import ast

# set path and log file name
base_dir = Path(__file__).resolve().parent

base_log_dir = os.getenv("LOG_DIR", f'{os.getenv("HOME")}/Logger/Master')
log_file = "logging.log"

base_image_dir = os.getenv("IMAGE_DIR", f'{os.getenv("HOME")}/Camera/Captures')
# create fastapi instance
app = FastAPI()

# set template and static file directories for Jinja
templates = Jinja2Templates(directory=str(Path(base_dir, "static")))
app.mount("/static", StaticFiles(directory="static"), name="static")

async def log_reader(log_file_path: str) -> str:
    """Log reader

    Args:
        log_file_path (str): Path to log file.

    Returns:
        str: JSON string of parsed log entries.
    """
    if not log_file_path:
        return json.dumps([{"level": "info", "message": "None", "raw": "None"}])
        
    full_path = f"{base_log_dir}/{log_file_path}"
    if not os.path.isfile(full_path):
        return json.dumps([{"level": "error", "message": "Log file not found.", "raw": "Log file not found."}])
        
    with open(full_path, "r") as file:
        lines = collections.deque(file)
        
    parsed_lines = []
    for line in lines:
        log_level = "info"
        if "ERROR" in line:
            log_level = "error"
        elif "WARNING" in line:
            log_level = "warning"
            
        is_image = False
        image_path = None
        is_json_file = False
        json_file_path = None
        
        if '.jpg' in line.lower() and 'path' in line.lower():
            image_path_raw = line.split(":")[-1].strip()
            if not any(c in image_path_raw for c in ['"', '{', '}']):
                is_image = True
                image_path = image_path_raw.replace(base_image_dir, '').replace('//', '/')
        elif '.json' in line and 'path' in line.lower():
            json_path_raw = line.split(":")[-1].strip()
            if not any(c in json_path_raw for c in ['"', '{', '}']):
                is_json_file = True
                json_file_path = json_path_raw.replace(base_image_dir, '').replace('//', '/')
            
        json_data = None
        message = line.strip()
        
        start_idx = line.find('{')
        end_idx = line.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            dict_str = line[start_idx:end_idx+1]
            try:
                json_obj = json.loads(dict_str)
                json_data = json_obj
                message = line[:start_idx].strip()
            except json.JSONDecodeError:
                try:
                    json_obj = ast.literal_eval(dict_str)
                    if isinstance(json_obj, dict):
                        json_data = json_obj
                        message = line[:start_idx].strip()
                except (SyntaxError, ValueError):
                    pass
                    
            if isinstance(json_data, dict):
                for k, v in json_data.items():
                    if isinstance(v, str) and v.strip().startswith('{') and v.strip().endswith('}'):
                        try:
                            json_data[k] = json.loads(v)
                        except json.JSONDecodeError:
                            pass
                
        parsed_lines.append({
            "level": log_level,
            "message": message,
            "json_data": json_data,
            "is_image": is_image,
            "image_path": image_path,
            "is_json_file": is_json_file,
            "json_file_path": json_file_path,
            "raw": line.strip()
        })
        
    parsed_lines.reverse()
    return json.dumps(parsed_lines)


@app.get("/")
async def get(request: Request) -> templates.TemplateResponse:
    log_file = "logging.log"
    context = {"title": "SMARTCAM Log Viewer", "log_file": log_file}
    return templates.TemplateResponse("index.html", {"request": request, "context": context})

@app.get("/history")
async def get_history(request: Request) -> templates.TemplateResponse:
    dates = []
    if os.path.exists(base_log_dir):
        for root, dirs, files in os.walk(base_log_dir):
            rel_path = os.path.relpath(root, base_log_dir)
            parts = rel_path.split(os.sep)
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                dates.append(rel_path.replace(os.sep, '/'))
    dates.sort(reverse=True)
    return templates.TemplateResponse("history.html", {"request": request, "dates": dates})

@app.get("/{year}/{month}/{day}")
async def get(
        year: str,
        month: str,
        day: str,
        request: Request
        
    ) -> templates.TemplateResponse:
    date_directory = f'{base_log_dir}/{year}/{month}/{day}'
    if not os.path.isdir(date_directory):
        return {"error": "Date directory not found"}
    log_files = [str(file.replace(base_log_dir, '')) for file in sorted(glob.glob(f"{date_directory}/*.log"))]
    return templates.TemplateResponse(
        "log_files.html",
        {"request": request, "year": year, "month": month, "day": day, "log_files": log_files},
    )
@app.get("/api/download")
async def download_log(file: str = "logging.log"):
    file_path = os.path.join(base_log_dir, urllib.parse.unquote(file))
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(file_path, filename=os.path.basename(file_path))

@app.get("/{year}/{month}/{day}/{name}")
async def get(
        year: str,
        month: str,
        day: str,
        name: str,
        request: Request
    ) -> templates.TemplateResponse:
    log_file = f'{year}/{month}/{day}/{name}'
    context = {"title": "SMARTCAM Log Viewer", "log_file": log_file}
    return templates.TemplateResponse("index.html", {"request": request, "context": context})


@app.get("/{year}/{month}/{day}/{path}/{name}")
async def get(
        year: str,
        month: str,
        day: str,
        path: str,
        name: str,
        request: Request
    ) -> FileResponse:
    image_file  = f'{base_image_dir}/{year}/{month}/{day}/{path}/{name}'
    if not os.path.isfile(image_file):
        return {"error": "Image not found"}
    return FileResponse(image_file)

@app.websocket("/ws/log")
async def websocket_endpoint_log(websocket: WebSocket, file: str = "logging.log") -> None:
    """WebSocket endpoint for client connections

    Args:
        websocket (WebSocket): WebSocket request from client.
        file (str): Log file to stream
    """
    await websocket.accept()

    try:
        while True:
            await asyncio.sleep(2)
            logs_json = await log_reader(file)
            await websocket.send_text(logs_json)
    except Exception as e:
        print(e)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

# set parameters to run uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        reload=True,
        workers=1,
    )
