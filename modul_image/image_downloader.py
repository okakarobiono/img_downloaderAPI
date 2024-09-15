import io
import json
import os
import cv2
import time
import requests
from urllib.parse import urlparse
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from modul_image.image_utils import resize_and_optimize_image, is_image_suitable
from modul_search import search_bing, search_images_ddg
from module_api_key.config_api import BING_API_KEY

console = Console()

def adjust_text_position(text, default_position, max_width, is_main_title=False, font=cv2.FONT_HERSHEY_SIMPLEX,
                         font_scale=1, thickness=2, line_spacing=10, img_width=1200, img_height=760):
    lines = []
    current_line = ""
    for word in text.split():
        test_line = current_line + " " + word if current_line else word
        (test_width, _), _ = cv2.getTextSize(test_line, font, font_scale, thickness)
        if test_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)

    total_height = sum([cv2.getTextSize(line, font, font_scale, thickness)[0][1] for line in lines]) + (
                len(lines) - 1) * line_spacing

    min_left_margin = 20
    max_right_margin = img_width - 20

    if is_main_title:
        new_x = max(min_left_margin, min(default_position[0],
                           max_right_margin - max(cv2.getTextSize(line, font, font_scale, thickness)[0][0] for line in lines)))
    else:
        new_x = max(min_left_margin, min(default_position[0], max_right_margin - cv2.getTextSize(lines[0], font, font_scale, thickness)[0][0]))

    new_y = max(total_height, min(default_position[1], img_height - 20))

    return (int(new_x), int(new_y)), lines

def loading_animation(message):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=message, total=None)
        time.sleep(1)  # Simulasi loading

async def download_image(query, main_title=None, website_title=None):
    console.print(f"[bold green]Received query:[/bold green] {query}")

    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    sources = [
        ("DuckDuckGo", lambda: search_images_ddg(query, max_images=50)),
        ("Bing", lambda: search_bing(query, BING_API_KEY)),
    ]

    for source_name, search_func in sources:
        loading_animation(f"Searching images on {source_name}...")
        try:
            results = search_func()
            if not results:
                console.print(f"[yellow]No results from {source_name}, moving to next source.[/yellow]")
                continue

            for image_url in results:
                if not image_url:
                    continue

                console.print(f"[cyan]Processing image: {image_url}[/cyan]")
                loading_animation(f"Downloading image from {source_name}...")
                try:
                    response = requests.get(image_url, stream=True)
                    response.raise_for_status()

                    image_data = io.BytesIO(response.content)

                    if is_image_suitable(image_data):
                        console.print(f"[bold green]Suitable image found from {source_name}![/bold green]")
                        console.print(f"[bold green]Image URL: {image_url}[/bold green]")
                        image_data.seek(0)

                        with open('config.json', 'r') as config_file:
                            config = json.load(config_file)

                        if 'mainTitle' not in config:
                            config['mainTitle'] = {'text': '', 'color': '', 'size': 0, 'padding': 0, 'position': {'left': 0, 'top': 0}}
                        if 'websiteTitle' not in config:
                            config['websiteTitle'] = {'text': '', 'color': '', 'size': 0, 'padding': 0, 'position': {'left': 0, 'top': 0}}

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
                            max_width,
                            is_main_title=True
                        )

                        website_title_pos = adjust_text_position(
                            config['config']['websiteTitle']['text'],
                            (config['config']['websiteTitle']['position']['left'],
                             config['config']['websiteTitle']['position']['top']),
                            max_width
                        )

                        config['config']['mainTitle']['position']['left'] = main_title_pos[0]
                        config['config']['websiteTitle']['position']['left'] = website_title_pos[0]

                        optimized_image_data = resize_and_optimize_image(image_data, template_path='template.webp', config=config)

                        def iterfile():
                            return iter(lambda: optimized_image_data.read(10 * 1024), b'')

                        parsed_url = urlparse(image_url)
                        filename = os.path.splitext(os.path.basename(parsed_url.path))[0] + ".webp"

                        return StreamingResponse(
                            iterfile(),
                            media_type="image/webp",
                            headers={"Content-Disposition": f"attachment; filename={filename}"}
                        )
                except Exception as e:
                    console.print(f"[red]Error downloading image from {image_url}: {str(e)}[/red]")
                    continue

        except Exception as e:
            console.print(f"[red]Error while processing {source_name}: {str(e)}[/red]")
            continue

    console.print("[bold red]No suitable image found from any source.[/bold red]")
    raise HTTPException(status_code=404, detail="No suitable image found from any source")