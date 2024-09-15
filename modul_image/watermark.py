from PIL import Image, ImageDraw, ImageFont


def add_watermark(base_image, template_path, config):
    # Load template
    template = Image.open(template_path).convert("RGBA")

    # Resize base image if needed
    if base_image.size != (1200, 760):
        base_image = base_image.resize((1200, 760), Image.Resampling.LANCZOS)

    # Ensure base_image is in RGBA mode
    base_image = base_image.convert('RGBA')

    # Composite base image and template
    composite = Image.alpha_composite(base_image, template)

    draw = ImageDraw.Draw(composite)

    for title_type in ['mainTitle', 'websiteTitle']:
        title_config = config['config'][title_type]
        text = title_config['text']
        color = title_config['color']
        font_size = title_config['size']
        position = title_config['position']

        try:
            font = ImageFont.truetype('font/Roboto-Bold.ttf', font_size)
        except IOError:
            font = ImageFont.load_default()

        x = position['left']
        y = position['top']

        # Draw text
        draw.text((x, y), text, font=font, fill=color)

    return composite