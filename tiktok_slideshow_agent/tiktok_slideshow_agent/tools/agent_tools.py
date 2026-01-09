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
    """Creates a timestamped project folder locally AND on Google Drive.
    
    Returns:
        A dictionary containing paths and IDs:
        - project_root_id: ID of the root folder on Drive.
        - local_project_root: Absolute local path to the project root.
        - local_slideshows_dir: Absolute local path for rendered images.
        - folder_name: The name of the root folder.
    """
    import datetime
    import re
    from pathlib import Path
    
    # Base Path Calculation (same as other tools)
    current_file = Path(__file__).resolve()
    # tools -> tiktok_slideshow_agent -> PROJECT_ROOT -> output
    base_path = current_file.parent.parent.parent
    output_base = base_path / "output"
    
    now = datetime.datetime.now()
    timestamp = now.strftime("%d%m%Y_%H%M")
    
    # Increase descriptiveness
    clean_topic = re.sub(r'[^a-zA-Z0-0\s]', '', topic)
    reel_name = clean_topic.replace(' ', '_').lower().strip()
    reel_name = reel_name[:40] 
    
    root_folder_name = f"{timestamp}_{reel_name}"
    
    # 1. Local Creation
    local_project_root = output_base / root_folder_name
    local_slideshows_dir = local_project_root / "slideshows"
    local_metadata_dir = local_project_root / "metadata"
    
    await asyncio.to_thread(os.makedirs, local_project_root, exist_ok=True)
    await asyncio.to_thread(os.makedirs, local_slideshows_dir, exist_ok=True)
    await asyncio.to_thread(os.makedirs, local_metadata_dir, exist_ok=True)
    
    # 2. Drive Creation (Target Folder ID specified by user)
    # Target ID: 1HQv0qrW1AUlUs2PWM3cQ572NyqonpLks
    TARGET_DRIVE_PARENT_ID = "1HQv0qrW1AUlUs2PWM3cQ572NyqonpLks"
    
    root_folder_id = await get_drive().create_folder(root_folder_name, parent_id=TARGET_DRIVE_PARENT_ID)
    
    # We don't strictly need to create subfolders on Drive if we just upload files to root_folder_id,
    # but maintaining structure is good.
    # Actually, to keep it simple for the agent, we can just upload all rendered slides to the root_folder_id.
    
    return {
        "project_root_id": root_folder_id,
        "local_project_root": str(local_project_root),
        "local_slideshows_dir": str(local_slideshows_dir),
        "local_metadata_dir": str(local_metadata_dir),
        "folder_name": root_folder_name
    }

@tool
async def save_locally(project_id: str, topic: str, slides: str, metadata_dir: str) -> str:
    """Save metadata locally and record in the Knowledge Base.
    
    Args:
        project_id: Unique identifier for the project.
        topic: The main topic of the slideshow.
        slides: A JSON string representing a list of slide objects.
        metadata_dir: The absolute path to the local metadata directory (or Drive ID, context dependent).
    """
    try:
        if isinstance(slides, list):
            slides_data = slides
        else:
            slides_data = json.loads(slides)
    except json.JSONDecodeError:
        return "Error: 'slides' argument must be a valid JSON string representing a list of slides."

    # 1. Save locally if metadata_dir looks like a path
    if os.path.exists(metadata_dir) or "/" in metadata_dir:
         metadata_path = os.path.join(metadata_dir, "metadata.json")
         def save_metadata_sync():
             with open(metadata_path, "w", encoding="utf-8") as f:
                 json.dump(slides_data, f, indent=4)
         await asyncio.to_thread(save_metadata_sync)

    # 2. Save to KB (historical record)
    await asyncio.to_thread(get_kb().save_slideshow, project_id, topic, slides_data, "Drive Upload")
    
    return f"Metadata recorded in Knowledge Base and saved to {metadata_dir}"

@tool
async def upload_to_drive(file_paths: list[str], folder_id: str) -> str:
    """Uploads files to a specific Google Drive folder.
    
    Args:
        file_paths: List of local absolute file paths to upload.
        folder_id: The Google Drive folder ID to upload into.
        
    Returns:
        A shared link to the folder containing the uploads.
    """
    return await get_drive().upload_files(file_paths, folder_id)

@tool
async def send_email_notification(subject: str, content: str, to_email: str = None) -> str:
    """Sends an email notification via Gmail.
    
    Args:
        subject: The email subject line.
        content: The body text of the email.
        to_email: The recipient's email address. Defaults to RECIPIENT_NOTIFICATION env var.
    """
    if to_email is None:
        to_email = os.getenv("RECIPIENT_NOTIFICATION")
    
    if not to_email:
        return "Error: No recipient email provided."
        
    return await get_drive().send_email(to_email, subject, content)
