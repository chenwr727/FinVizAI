import base64
import os
from typing import List

import mistune
from pyppeteer import launch
from tqdm import tqdm

INITIAL_FONT_SIZE = 28
MIN_FONT_SIZE = 18
INITIAL_H1_FONT_SIZE = 56
MIN_H1_FONT_SIZE = 36

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
html, body {{
    margin: 0;
    padding: 0;
    width: 1080px;
    height: 1920px;
    font-family: 'Roboto', sans-serif;
    overflow: hidden;
    position: relative;
}}

body::before {{
    content: "";
    position: absolute;
    width: 100%;
    height: 100%;
    background: url('data:image/png;base64,{encoded_string}') no-repeat center center;
    background-size: cover;
    filter: blur({blur}px);
    z-index: 0;
}}

.overlay {{
    position: relative;
    z-index: 1;
    width: 100%;
    height: 100%;
}}

.container {{
    width: 90%;
    margin: 40px auto;
    padding: 30px;
    background: rgba(255, 255, 255, 0.85);
    border-radius: 16px;
    box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
    font-size: {initial_font_size}px;
    line-height: 1.5;
    box-sizing: border-box;
    opacity: {opacity};
    transition: opacity 0.3s ease;
}}

h1 {{
    font-size: {initial_h1_font_size}px;
    color: #0078d7;
    text-align: center;
}}

strong {{
    color: #f08c00;
    font-weight: bold;
}}

ul {{
    padding-left: 2em;
}}

li {{
    margin-bottom: 0.5em;
}}

p {{
    margin-bottom: 1em;
    color: #333;
}}
</style>
<script>
window.onload = function() {{
    const container = document.querySelector('.container');
    const containerHeight = container.scrollHeight;
    const containerTop = container.getBoundingClientRect().top;
    const availableHeight = window.innerHeight - (containerTop * 2);
    const maxHeight = availableHeight;

    if (containerHeight > maxHeight) {{
        let currentFontSize = {initial_font_size};
        const minFontSize = {min_font_size};

        while (container.scrollHeight > maxHeight && currentFontSize > minFontSize) {{
            currentFontSize -= 0.5;
            container.style.fontSize = currentFontSize + 'px';
        }}

        const h1Elements = document.querySelectorAll('h1');
        if (h1Elements.length > 0) {{
            const h1FontSize = Math.max({min_h1_font_size}, Math.floor(currentFontSize * 2));
            h1Elements.forEach(h1 => {{
                h1.style.fontSize = h1FontSize + 'px';
            }});
        }}
    }}
}};
</script>
</head>
<body>
<div class="overlay">
    <div class="container">{html_content}</div>
</div>
</body>
</html>
"""


async def generate_report_frames(
    md_text: str, background_image_path: str, output_dir: str, total_frames: int = 20
) -> List[str]:
    os.makedirs(output_dir, exist_ok=True)

    with open(background_image_path, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode("utf-8")

    html_content = mistune.html(md_text)

    browser = await launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
    page = await browser.newPage()
    await page.setViewport({"width": 1080, "height": 1920})

    output_paths = []
    for frame in tqdm(range(1, total_frames + 1), desc="Generating frames"):
        output_path = os.path.join(output_dir, f"frame_{frame:03}.png")
        if os.path.exists(output_path):
            output_paths.append(output_path)
            continue

        progress = (frame / total_frames) ** 2
        opacity = round(1.0 - progress, 3)
        blur = round(8 * (1 - progress), 2)

        html = HTML_TEMPLATE.format(
            encoded_string=encoded_string,
            initial_font_size=INITIAL_FONT_SIZE,
            min_font_size=MIN_FONT_SIZE,
            initial_h1_font_size=INITIAL_H1_FONT_SIZE,
            min_h1_font_size=MIN_H1_FONT_SIZE,
            html_content=html_content,
            opacity=opacity,
            blur=blur,
        )

        temp_html_path = f"temp_frame_{frame:03}.html"
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html)

        await page.goto(f"file://{os.path.abspath(temp_html_path)}")
        await page.waitForSelector(".container")

        await page.screenshot({"path": output_path, "fullPage": True})

        os.remove(temp_html_path)
        output_paths.append(output_path)

    await browser.close()
    return output_paths
