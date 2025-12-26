from langchain_core.tools import tool
import json
from tiktok_slideshow_agent.tools.images import ImageLibraryTool
from tiktok_slideshow_agent.tools.renderer import PlaywrightRendererTool
from tiktok_slideshow_agent.tools.drive import GoogleDriveTool
from tiktok_slideshow_agent.tools.knowledge import KnowledgeBaseTool

# Initialize Tool Instances
image_lib = ImageLibraryTool()
renderer = PlaywrightRendererTool()
drive = GoogleDriveTool()
kb = KnowledgeBaseTool()

@tool
def search_images(query: str) -> str:
    """Search for images in the library based on tags.
    
    Args:
        query: The tag or keyword to search for.
    """
    results = image_lib.search_images(query_tags=[query])
    return str(results)

@tool
def render_slide(text: str, image_path: str, slide_number: int) -> str:
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
    return renderer.render_slide(slide_data, config)

@tool
def upload_and_save(project_id: str, topic: str, slides: str) -> str:
    """Upload slides to Drive and save to Knowledge Base.
    
    Args:
        project_id: Unique identifier for the project.
        topic: The main topic of the slideshow.
        slides: A JSON string representing a list of slide objects. 
                Each object should have 'text' and 'image_path'.
    """
    try:
        if isinstance(slides, list):
            slides_data = slides
        else:
            slides_data = json.loads(slides)
    except json.JSONDecodeError:
        return "Error: 'slides' argument must be a valid JSON string representing a list of slides."

    # Create folder
    folder_id = drive.create_folder(f"{project_id}_{topic}")
    
    # Upload
    files = [s.get("image_path") for s in slides_data if s.get("image_path")]
    link = drive.upload_files(files, folder_id)
    
    # Save to KB
    kb.save_slideshow(project_id, topic, slides_data, link)
    return link
