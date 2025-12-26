import os
from playwright.sync_api import sync_playwright

class PlaywrightRendererTool:
    def __init__(self, output_dir: str = "output"):
        self.base_path = "/Users/mindreader/Desktop/deepagents-quickstarts/tiktok_slideshow_agent"
        self.output_dir = os.path.join(self.base_path, output_dir)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def render_slide(self, slide_data: dict, project_config: dict) -> str:
        """
        Generates HTML for the slide and captures a screenshot.
        Returns the path to the generated image.
        """
        image_path = slide_data["image_path"]
        text = slide_data["text"]
        slide_num = slide_data["slide_number"]
        font = project_config.get("font_style", "Arial")
        
        # Simple template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
                body {{
                    margin: 0;
                    padding: 0;
                    width: 1080px;
                    height: 1920px;
                    background-image: url('file://{image_path}');
                    background-size: cover;
                    background-position: center;
                    font-family: 'Montserrat', sans-serif;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    text-align: center;
                    color: white;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
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
            <div class="overlay"></div>
            <div class="content">
                {text}
            </div>
        </body>
        </html>
        """
        
        output_filename = f"slide_{slide_num}.png"
        output_path = os.path.join(self.output_dir, output_filename)
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1080, "height": 1920})
            page.set_content(html_content)
            page.screenshot(path=output_path)
            browser.close()
            
        return output_path
