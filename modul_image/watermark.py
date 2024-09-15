from PIL import Image, ImageDraw, ImageFont
import textwrap

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
        bg_color = title_config.get('backgroundColor')

        try:
            font = ImageFont.truetype('font/Roboto-Bold.ttf', font_size)
        except IOError:
            font = ImageFont.load_default()

        x = position['left']
        y = position['top']

        # Adjust text position
        max_width = 1200 - 2 * 15  # Maximum width in pixels for the text, with 15px padding on each side
        wrapped_text = textwrap.wrap(text, width=int(max_width / font_size * 2))  # Estimate characters per line
        text_width, text_height = max(draw.textbbox((0, 0), line, font=font)[2] for line in wrapped_text), sum(
            draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in wrapped_text)

        if title_type == 'mainTitle':
            x = max(15, min(x, 1200 - text_width - 15))
            y = max(15, min(y, 760 - text_height - 15))
        else:
            x = max(15, min(x, 1200 - text_width - 15))
            y = max(text_height + 15, min(y, 760 - 15))

        lines = wrapped_text

        # Truncate text if it's too long
        max_lines = 5  # Adjust this value as needed
        if len(lines) > max_lines:
            lines = lines[:max_lines - 1] + [lines[max_lines - 1][:-3] + '...']

        # Calculate line height using font metrics
        ascent, descent = font.getmetrics()
        line_height = ascent + descent
        padding = 15  # Padding between lines

        # Calculate total height of the text block
        total_height = (line_height + padding) * len(lines) - padding

        # Adjust y position to center the text block
        y -= total_height // 2

        # Draw background and text
        x += padding
        if bg_color:
            for i, line in enumerate(lines):
                line_y = y + i * (line_height + padding)
                text_bbox = draw.textbbox((x, line_y), line, font=font)
                padded_bbox = (
                    text_bbox[0] - padding,
                    text_bbox[1] - padding,
                    text_bbox[2] + padding,
                    text_bbox[3] + padding
                )
                draw.rectangle(padded_bbox, fill=bg_color)

        for i, line in enumerate(lines):
            line_y = y + i * (line_height + padding)
            draw.text((x, line_y), line, font=font, fill=color)

    return composite