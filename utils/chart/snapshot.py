import asyncio
import base64
import os

from pyppeteer.browser import Browser

SNAPSHOT_JS = (
    "echarts.getInstanceByDom(document.querySelector('div[_echarts_instance_]'))."
    "getDataURL({type: '%s', pixelRatio: %s, excludeComponents: ['toolbox']})"
)


async def make_snapshot(browser: Browser, html_file: str, image_file: str, pixel_ratio: int = 2, delay: int = 2):
    html_path = "file://" + os.path.abspath(html_file)
    file_type = image_file.split(".")[-1]

    page = await browser.newPage()
    await page.setJavaScriptEnabled(enabled=True)
    await page.goto(html_path)
    await asyncio.sleep(delay)

    snapshot_js = SNAPSHOT_JS % (file_type, pixel_ratio)
    content: str = await page.evaluate(snapshot_js)

    content_array = content.split(",")
    image_data = decode_base64(content_array[1])

    save_as_png(image_data, image_file)


def decode_base64(data: str) -> bytes:
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += "=" * (4 - missing_padding)
    return base64.decodebytes(data.encode("utf-8"))


def save_as_png(image_data: bytes, output_name: str):
    with open(output_name, "wb") as f:
        f.write(image_data)
