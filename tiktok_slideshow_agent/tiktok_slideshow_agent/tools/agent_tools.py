from langchain_core.tools import tool
import json
import os
from tiktok_slideshow_agent.tools.images import ImageLibraryTool
from tiktok_slideshow_agent.tools.renderer import PlaywrightRendererTool
from tiktok_slideshow_agent.tools.drive import GoogleDriveTool
from tiktok_slideshow_agent.tools.knowledge import KnowledgeBaseTool

# Lazy Tool Getters to avoid BlockingError during import
_image_lib = None
_renderer = None
_drive = None
_kb = None

def get_image_lib():
    global _image_lib
    if _image_lib is None:
        _image_lib = ImageLibraryTool()
    return _image_lib

def get_renderer():
    global _renderer
    if _renderer is None:
        _renderer = PlaywrightRendererTool()
    return _renderer

def get_drive():
    global _drive
    if _drive is None:
        _drive = GoogleDriveTool()
    return _drive

def get_kb():
    global _kb
    if _kb is None:
        _kb = KnowledgeBaseTool()
    return _kb

import asyncio

@tool
async def render_slide(text: str, image_path: str, slide_number: int) -> str:
    """Render a slide with text and image, returning the output path.
    
    Args:
        text: The overlay text for the slide.
        image_path: The absolute path to the background image.
        slide_number: The sequence number of the slide.
    """
    slide_data = {
        "text": text,
        "image_path": image_path,
        "slide_number": slide_number
    }
    # Config can be expanded later
    config = {"font_style": "Montserrat"} 
    
    # Run async renderer
    return await get_renderer().render_slide(slide_data, config)

@tool
async def save_locally(project_id: str, topic: str, slides: str) -> str:
    """Save slides locally and record in the Knowledge Base.
    
    Args:
        project_id: Unique identifier for the project.
        topic: The main topic of the slideshow.
        slides: A JSON string representing a list of slide objects. 
                Each object should have 'text' and 'image_path'.
    """
    import datetime
    import re
    
    try:
        if isinstance(slides, list):
            slides_data = slides
        else:
            slides_data = json.loads(slides)
    except json.JSONDecodeError:
        return "Error: 'slides' argument must be a valid JSON string representing a list of slides."

    # 1. Format folder name: DDMMYYYY_HHMM_topic
    now = datetime.datetime.now()
    timestamp = now.strftime("%d%m%Y_%H%M")
    
    # Clean and truncate topic
    clean_topic = re.sub(r'[^a-zA-Z0-0\s]', '', topic)
    reel_name = clean_topic.replace(' ', '_').lower()[:12]
    
    root_folder_name = f"{timestamp}_{reel_name}"
    root_folder_path = await asyncio.to_thread(get_drive().create_folder, root_folder_name)
    
    # 2. Create standardized subfolders
    slideshows_folder = await asyncio.to_thread(get_drive().create_folder, os.path.join(root_folder_name, "slideshows"))
    metadata_folder = await asyncio.to_thread(get_drive().create_folder, os.path.join(root_folder_name, "metadata"))
    
    # 3. Save metadata.json for reproducibility
    metadata_path = os.path.join(metadata_folder, "metadata.json")
    def save_metadata():
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(slides_data, f, indent=4)
    
    await asyncio.to_thread(save_metadata)
    
    # 4. Move rendered images to the local 'slideshows' folder
    image_files = [s.get("image_path") for s in slides_data if s.get("image_path")]
    local_path = await asyncio.to_thread(get_drive().upload_files, image_files, slideshows_folder)
    
    # 5. Save to KB (historical record)
    await asyncio.to_thread(get_kb().save_slideshow, project_id, topic, slides_data, local_path)
    
    return f"Slideshow saved locally to: {root_folder_path}"
