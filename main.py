import os
import glob
from pathlib import Path
from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

import uvicorn
import asyncio

# set path and log file name
base_dir = Path(__file__).resolve().parent

base_log_dir = f'{os.getenv("HOME")}/Logger/Master'
log_file = "logging.log"

base_image_dir = f'{os.getenv("HOME")}/Camera/Captures'
# create fastapi instance
app = FastAPI()

# set template and static file directories for Jinja
templates = Jinja2Templates(directory=str(Path(base_dir, "static")))
app.mount("/static", StaticFiles(directory="static"), name="static")

async def log_reader(n=5) -> list:
    """Log reader

    Args:
        n (int, optional): number of lines to read from file. Defaults to 5.

    Returns:
        list: List containing last n-lines in log file with html tags.
    """
    log_lines = []
    with open(f"{base_log_dir}/{log_file}", "r") as file:
        for line in file.readlines():
            if line.__contains__("ERROR"):
                log_lines.append(f'<span style="color: red;">{line}</span><br/>')
            elif line.__contains__("WARNING"):
                log_lines.append(f'<span style="color: orange;"">{line}</span><br/>')
            elif line.__contains__('jpg'):
                image_path = line.split(":")[-1].strip()
                image_path = image_path.replace(base_image_dir, '')
                log_lines.append(f'<a href="{image_path}" target="_blank">{line}</a><br/>')
            else:
                log_lines.append(f"{line}<br/>")
    return log_lines


@app.get("/")
async def get(request: Request) -> templates.TemplateResponse:
    context = {"title": "SMARTCAM Log Viewer", "log_file": log_file}
    return templates.TemplateResponse("index.html", {"request": request, "context": context})

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
    log_files = [str(file.replace(base_log_dir, '')) for file in glob.glob(f"{date_directory}/*.log")]
    print(log_files)
    return templates.TemplateResponse(
        "log_files.html",
        {"request": request, "year": year, "month": month, "day": day, "log_files": log_files},
    )

@app.get("/{year}/{month}/{day}/{name}")
async def get(
        year: str,
        month: str,
        day: str,
        name: str,
        request: Request
    ) -> templates.TemplateResponse:
    log_file  = f'/{year}/{month}/{day}/{name}'
    
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
async def websocket_endpoint_log(websocket: WebSocket) -> None:
    """WebSocket endpoint for client connections

    Args:
        websocket (WebSocket): WebSocket request from client.
    """
    await websocket.accept()

    try:
        while True:
            await asyncio.sleep(2)
            logs = await log_reader(100)
            await websocket.send_text(logs)
    except Exception as e:
        print(e)
    finally:
        await websocket.close()

# set parameters to run uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        reload=True,
        workers=1,
    )
