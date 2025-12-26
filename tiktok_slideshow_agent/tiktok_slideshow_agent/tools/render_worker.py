import asyncio
import os
import sys
import json
from playwright.async_api import async_playwright

async def render_worker(slide_data_json: str, output_path: str, fonts_dir: str):
    slide_data = json.loads(slide_data_json)
    image_path = slide_data["image_path"]
    text = slide_data["text"]
    
    font_bold = os.path.join(fonts_dir, "TikTokSans-Bold.ttf")
    font_regular = os.path.join(fonts_dir, "TikTokSans-Regular.ttf")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @font-face {{
                font-family: 'TikTok Sans';
                src: url('file://{font_regular}');
                font-weight: normal;
            }}
            @font-face {{
                font-family: 'TikTok Sans';
                src: url('file://{font_bold}');
                font-weight: bold;
            }}
            body {{
                margin: 0;
                padding: 0;
                width: 1080px;
                height: 1920px;
                background-color: black;
                font-family: 'TikTok Sans', sans-serif;
                overflow: hidden;
            }}
            .slide-container {{
                width: 1080px;
                height: 1920px;
                background-image: url('file://{image_path}');
                background-size: cover;
                background-position: center;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                color: white;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
                position: relative;
            }}
            .overlay {{
                background: rgba(0, 0, 0, 0.3);
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 1;
            }}
            .content {{
                z-index: 2;
                padding: 100px;
                font-size: 80px;
                font-weight: bold;
                line-height: 1.2;
            }}
        </style>
    </head>
    <body>
        <div class="slide-container">
            <div class="overlay"></div>
            <div class="content">
                {text}
            </div>
        </div>
    </body>
    </html>
    """

    # Save HTML to a temp file in the same directory as output to avoid path issues
    temp_html = output_path + ".temp.html"
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1080, "height": 1920})
            
            # Load the HTML file
            await page.goto(f"file://{temp_html}", timeout=30000)
            
            # Wait for fonts/assets to settle
            await page.wait_for_timeout(1000)
            
            # Targeted screenshot
            slide_container = await page.query_selector(".slide-container")
            if slide_container:
                await slide_container.screenshot(path=output_path)
            else:
                await page.screenshot(path=output_path)
            
            await browser.close()
            print(f"SUCCESS:{output_path}")
    finally:
        if os.path.exists(temp_html):
            os.remove(temp_html)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python render_worker.py <slide_data_json> <output_path> <fonts_dir>")
        sys.exit(1)
    
    asyncio.run(render_worker(sys.argv[1], sys.argv[2], sys.argv[3]))
