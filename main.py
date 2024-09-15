import logging
import io
import os
import json
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastbook import search_images_ddg
from PIL import Image
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from starlette.middleware.cors import CORSMiddleware
from modul_image.image_utils import resize_and_optimize_image
from modul_search import search_bing
from modul_search.blocked_domains import BLOCKED_DOMAINS
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
import time
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout
import ssl
import certifi
from urllib.parse import urlparse
import asyncio
from fastbook import search_images_ddg
from modul_search import search_bing, search_pexels, search_pixabay
from modul_search.ddg_search import async_search_images_ddg
from module_api_key.config_api import PEXELS_API_KEY, PIXABAY_API_KEY, BING_API_KEY
import cv2
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
import aiohttp
from aiohttp import ClientError
from fastapi.staticfiles import StaticFiles
from typing import Optional

certifi_path = certifi.where()
app = FastAPI(
    title="Image Downloader API",
    description="API to download images based on search queries from various sources",
    version="1.0.1"
)

API_KEYS = {
    "Bing": BING_API_KEY,
    "Pexels": PEXELS_API_KEY,
    "Pixabay": PIXABAY_API_KEY
}

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Position(BaseModel):
    left: int
    top: int


class TitleConfig(BaseModel):
    text: str
    color: str
    size: int
    padding: int
    position: Position
    backgroundColor: Optional[str] = None

class Config(BaseModel):
    mainTitle: TitleConfig
    websiteTitle: TitleConfig

CONFIG_FILE_PATH = 'config.json'

def load_config_from_file():
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, 'r') as file:
            return json.load(file)
    return {}

def save_config_to_file(config):
    with open(CONFIG_FILE_PATH, 'w') as file:
        json.dump(config, file)

config_store = load_config_from_file()
config = load_config_from_file().get("config", {})

@app.post("/save-configuration")
async def save_configuration(config: Config):
    config_store["config"] = config.model_dump()
    save_config_to_file(config_store)
    return {"message": "Configuration saved successfully"}

@app.get("/load-configuration")
async def load_configuration():
    if "config" not in config_store:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config_store["config"]

# Konfigurasi logging dengan Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("rich")

def is_image_suitable(image_data, min_width=1200):
    try:
        with Image.open(image_data) as img:
            width, height = img.size
            return width >= min_width and width > height
    except Exception as e:
        logger.error(f"Error checking image suitability: {str(e)}")
        return False

def is_blocked_domain(url):
    domain = urlparse(url).netloc
    return any(blocked_domain in domain for blocked_domain in BLOCKED_DOMAINS)

async def download_and_check_image(image_url, timeout=20):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, ssl=ssl.create_default_context(cafile=certifi_path), timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                response.raise_for_status()
                image_data = io.BytesIO(await response.read())
                if is_image_suitable(image_data):
                    return image_data, response.headers.get('content-type')
                else:
                    logger.warning(f"Image not suitable: {image_url}")
                    return None, None
    except aiohttp.ClientConnectorError as e:
        logger.error(f"Connection error for {image_url}: {str(e)}")
    except aiohttp.ClientResponseError as e:
        logger.error(f"HTTP error {e.status} for {image_url}: {e.message}")
    except aiohttp.ClientPayloadError as e:
        logger.error(f"Payload error for {image_url}: {str(e)}")
    except aiohttp.ClientError as e:
        logger.error(f"Client error for {image_url}: {str(e)}")
    except ssl.SSLError as e:
        logger.error(f"SSL error for {image_url}: {str(e)}")
    except asyncio.TimeoutError:
        logger.error(f"Timeout error for {image_url}")
    except Exception as e:
        logger.exception(f"Unexpected error downloading image from {image_url}: {str(e)}")
    return None, None

def process_image(image_data):
    result = resize_and_optimize_image(image_data, template_path='template.webp', config=config)

def search_wikimedia(query, max_images=20):
    url = f"https://commons.wikimedia.org/w/index.php?search={query}&title=Special:MediaSearch&go=Go&type=image"
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Error fetching Wikimedia images: {response.status_code}")
        return []
    soup = BeautifulSoup(response.content, 'html.parser')
    images = soup.find_all('img', class_='sd-image')
    return [img['src'] for img in images[:max_images]]

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Image Downloader API V.1.0.1 Beta by Okaka 2024",
        "endpoints": {"Kasih tau Ga yaah, hmmm "
        }
    }

# Fungsi untuk animasi loading
def loading_animation(message):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=message, total=None)
        time.sleep(1)  # Simulasi loading

console = Console()

def adjust_text_position(text, position, max_width):
    text_length = len(text)
    base_left = position[0]

    if text_length > 20:
        new_left = max(0, base_left - (text_length - 20) * 10)
    else:
        new_left = base_left

    new_left = min(new_left, max_width - (text_length * 10))
    return (new_left, position[1])


import asyncio


@app.get("/download-image", response_class=StreamingResponse)
async def download_image(
        query: str = Query(..., min_length=1, description="Search query for the image"),
        main_title: str = Query(None, description="Text for the main title watermark"),
        website_title: str = Query(None, description="Text for the website title watermark"),
        filename: str = Query(None, description="Custom filename for the downloaded image")
):
    console.print(f"[bold green]Received query:[/bold green] {query}")

    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    async def process_image_source(source_name, search_func):
        try:
            results = await search_func(query, API_KEYS.get(source_name)) if asyncio.iscoroutinefunction(
                search_func) else search_func(query, API_KEYS.get(source_name))

            async def process_single_image(image_url):
                image_data, content_type = await download_and_check_image(image_url)
                if image_data:
                    return image_url, image_data, content_type
                return None

            image_tasks = [process_single_image(url) for url in results if url]
            processed_images = await asyncio.gather(*image_tasks)
            return [img for img in processed_images if img]
        except Exception as e:
            console.print(f"[red]Error while processing {source_name}: {str(e)}[/red]")
            return []

    sources = [
        ("DuckDuckGo", async_search_images_ddg),
        ("Pexels", search_pexels),
        #("Pixabay", search_pixabay),
        ("Bing", search_bing)
    ]

    all_results = await asyncio.gather(*[process_image_source(name, func) for name, func in sources])
    valid_images = [img for source_results in all_results for img in source_results]

    for source_name, source_results in zip([s[0] for s in sources], all_results):
        for image_url, image_data, content_type in source_results:
            if not image_url:
                continue
            console.print(f"[cyan]Processing image: {image_url}[/cyan]")
            try:
                if image_data:
                    console.print(f"[bold green]Suitable image found from {source_name}![/bold green]")
                    console.print(f"[bold green]Image URL: {image_url}[/bold green]")

                    with open('config.json', 'r') as config_file:
                        config = json.load(config_file)

                    if 'mainTitle' not in config:
                        config['mainTitle'] = {'text': '', 'color': '', 'size': 0, 'padding': 0,
                                               'position': {'left': 0, 'top': 0}}
                    if 'websiteTitle' not in config:
                        config['websiteTitle'] = {'text': '', 'color': '', 'size': 0, 'padding': 0,
                                                  'position': {'left': 0, 'top': 0}}

                    if main_title:
                        config['config']['mainTitle']['text'] = main_title
                    if website_title:
                        config['config']['websiteTitle']['text'] = website_title

                    img_width, img_height = 1200, 760
                    max_width = img_width * 0.8

                    main_title_pos = adjust_text_position(
                        config['config']['mainTitle']['text'],
                        (config['config']['mainTitle']['position']['left'],
                         config['config']['mainTitle']['position']['top']),
                        max_width
                    )

                    config['config']['mainTitle']['position']['left'] = main_title_pos[0]

                    optimized_image_data = resize_and_optimize_image(image_data, template_path='template.webp',
                                                                     config=config)

                    def iterfile():
                        return iter(lambda: optimized_image_data.read(10 * 1024), b'')

                    if filename:
                        filename = f"{filename}.webp"
                    else:
                        filename = f"image_{query.replace(' ', '_')}.webp"

                    return StreamingResponse(
                        iterfile(),
                        media_type="image/webp",
                        headers={"Content-Disposition": f"attachment; filename={filename}"}
                    )
            except RequestException as e:
                if isinstance(e, HTTPError):
                    console.print(f"[red]HTTP Error occurred while downloading image from {image_url}: {str(e)}[/red]")
                elif isinstance(e, ConnectionError):
                    console.print(
                        f"[red]Connection Error occurred while downloading image from {image_url}: {str(e)}[/red]")
                elif isinstance(e, Timeout):
                    console.print(f"[red]Timeout occurred while downloading image from {image_url}: {str(e)}[/red]")
                else:
                    console.print(
                        f"[red]An unexpected error occurred while downloading image from {image_url}: {str(e)}[/red]")
                continue

    console.print("[bold red]No suitable image found from any source.[/bold red]")
    raise HTTPException(status_code=404, detail="No suitable image found from any source")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)