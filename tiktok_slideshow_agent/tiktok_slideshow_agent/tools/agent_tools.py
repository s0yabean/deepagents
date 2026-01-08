from langchain_core.tools import tool
import json
import os
from tiktok_slideshow_agent.tools.images import ImageLibraryTool
from tiktok_slideshow_agent.tools.renderer import PlaywrightRendererTool
from tiktok_slideshow_agent.tools.drive import GoogleDriveTool
from tiktok_slideshow_agent.tools.drive import GoogleDriveTool
from tiktok_slideshow_agent.tools.knowledge import KnowledgeBaseTool
from tiktok_slideshow_agent.tools.sync_tool import sync_image_library

# Lazy Tool Getters to avoid BlockingError during import
_image_lib = None
_renderer = None
_drive = None
_kb = None
_sync_tool = None

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

def get_sync_tool():
    global _sync_tool
    if _sync_tool is None:
        _sync_tool = sync_image_library
    return _sync_tool

import asyncio

@tool
async def render_slide(text: str, image_path: str, slide_number: int, output_dir: str = None) -> str:
    """Render a slide with text and image, returning the output path.
    
    Args:
        text: The overlay text for the slide.
        image_path: The absolute path to the background image.
        slide_number: The sequence number of the slide.
        output_dir: Optional absolute path to the directory where the slide should be saved.
    """
    slide_data = {
        "text": text,
        "image_path": image_path,
        "slide_number": slide_number
    }
    # Config can be expanded later
    config = {"font_style": "Montserrat"} 
    
    # Run async renderer
    return await get_renderer().render_slide(slide_data, config, output_dir=output_dir)

@tool
async def setup_project_folder(topic: str) -> dict:
    """Creates a timestamped project folder and standardized subfolders.
    
    Returns:
        A dictionary containing absolute paths:
        - project_root: The root folder (DDMMYYYY_HHMM_topic)
        - slideshows_dir: Subfolder for rendered images.
        - metadata_dir: Subfolder for metadata.json.
    """
    import datetime
    import re
    
    now = datetime.datetime.now()
    timestamp = now.strftime("%d%m%Y_%H%M")
    
    # Increase descriptiveness: Target 15-40 chars for the topic portion
    clean_topic = re.sub(r'[^a-zA-Z0-0\s]', '', topic)
    reel_name = clean_topic.replace(' ', '_').lower().strip()
    # Take a healthy slice to ensure descriptiveness without hitting OS path limits
    reel_name = reel_name[:40] 
    
    root_folder_name = f"{timestamp}_{reel_name}"
    root_folder_path = await asyncio.to_thread(get_drive().create_folder, root_folder_name)
    
    slideshows_dir = await asyncio.to_thread(get_drive().create_folder, os.path.join(root_folder_name, "slideshows"))
    metadata_dir = await asyncio.to_thread(get_drive().create_folder, os.path.join(root_folder_name, "metadata"))
    
    return {
        "project_root": root_folder_path,
        "slideshows_dir": slideshows_dir,
        "metadata_dir": metadata_dir,
        "folder_name": root_folder_name
    }

@tool
async def save_locally(project_id: str, topic: str, slides: str, metadata_dir: str) -> str:
    """Save metadata locally and record in the Knowledge Base.
    
    Args:
        project_id: Unique identifier for the project.
        topic: The main topic of the slideshow.
        slides: A JSON string representing a list of slide objects.
        metadata_dir: The absolute path to the project's metadata directory.
    """
    try:
        if isinstance(slides, list):
            slides_data = slides
        else:
            slides_data = json.loads(slides)
    except json.JSONDecodeError:
        return "Error: 'slides' argument must be a valid JSON string representing a list of slides."

    # 1. Save metadata.json for reproducibility
    metadata_path = os.path.join(metadata_dir, "metadata.json")
    def save_metadata_sync():
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(slides_data, f, indent=4)
    
    await asyncio.to_thread(save_metadata_sync)
    
    # 2. Save to KB (historical record)
    # local_path here is used for KB reference, use metadata_dir or project_root
    project_root = os.path.dirname(metadata_dir)
    await asyncio.to_thread(get_kb().save_slideshow, project_id, topic, slides_data, project_root)
    
    return f"Metadata and KB record saved to: {project_root}"
