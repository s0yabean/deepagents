import json
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage
from .state import AgentState, Slide
from .prompts import (
    HOOK_GENERATION_PROMPT,
    CONTENT_GENERATION_PROMPT,
    IMAGE_SELECTION_PROMPT,
)
from .tools import (
    ImageLibraryTool,
    PlaywrightRendererTool,
    GoogleDriveTool,
    KnowledgeBaseTool,
)


def _is_black_image(image_path: str, threshold: float = 0.95) -> bool:
    """Check if an image is mostly black (likely failed to load).

    Args:
        image_path: Path to the image file
        threshold: Percentage of dark pixels to consider "black" (default 95%)

    Returns:
        True if image is mostly black, False otherwise
    """
    try:
        from PIL import Image

        img = Image.open(image_path)
        img = img.convert("RGB")
        pixels = list(img.getdata())
        dark_pixels = sum(1 for p in pixels if sum(p) < 30)  # Very dark pixels
        dark_ratio = dark_pixels / len(pixels)
        return dark_ratio > threshold
    except Exception as e:
        print(f"Warning: Could not check image brightness: {e}")
        return False  # Assume valid if we can't check


def _resolve_image_path(image_path: str, image_tool: ImageLibraryTool) -> str:
    """Resolve virtual image path to absolute filesystem path.

    Args:
        image_path: The image path (virtual or absolute)
        image_tool: ImageLibraryTool instance

    Returns:
        Resolved absolute path
    """
    # If it's a URL, return as-is (will be downloaded)
    if image_path.startswith("http://") or image_path.startswith("https://"):
        return image_path

    # Resolve virtual paths like /image_library/category/image.jpg
    if image_path.startswith("/image_library/"):
        resolved = image_path.replace(
            "/image_library/", str(image_tool.output_dir) + "/"
        )
    else:
        resolved = image_path

    return resolved


def _validate_image_exists(image_path: str) -> tuple[bool, str]:
    """Validate that an image exists and is not black.

    Args:
        image_path: The absolute path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if file exists
    if not os.path.exists(image_path):
        return (
            False,
            f"IMAGE_NOT_FOUND: Image file does not exist at path: {image_path}",
        )

    # Check if image is black (failed to load or broken)
    if _is_black_image(image_path, threshold=0.95):
        return (
            False,
            f"IMAGE_INVALID: Image appears to be black/invalid at path: {image_path}",
        )

    return True, ""


# Initialize Tools
image_tool = ImageLibraryTool()
renderer_tool = PlaywrightRendererTool()
drive_tool = GoogleDriveTool()
kb_tool = KnowledgeBaseTool()


class MockLLM:
    def invoke(self, messages):
        content = messages[0].content
        if "Hook" in content:
            return type(
                "obj",
                (object,),
                {
                    "content": """
            [
                {"text": "Mock Hook 1: The Secret to Success", "score": 9, "reason": "High curiosity"},
                {"text": "Mock Hook 2: Why you are failing", "score": 8, "reason": "Negative bias"}
            ]
            """
                },
            )
        elif "Storyteller" in content:
            return type(
                "obj",
                (object,),
                {
                    "content": """
            [
                "Slide 2: Consistency is key.",
                "Slide 3: Don't give up.",
                "Slide 4: Just do it.",
                "Follow for more."
            ]
            """
                },
            )
        elif "visual director" in content:
            # Return a valid ID from images.json
            return type("obj", (object,), {"content": "motivational_01"})
        return type("obj", (object,), {"content": ""})


# Initialize LLM (Mock for now due to API issues)
# llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
llm = MockLLM()


def orchestrator_node(state: AgentState):
    """
    Sets up initial configuration if not present.
    """
    print(f"--- Orchestrator: Starting project {state['project_id']} ---")
    # Default config if not provided (in a real app, load from a config file/DB)
    if not state.get("slide_count"):
        state["slide_count"] = 5
    if not state.get("tone"):
        state["tone"] = "Inspirational"
    if not state.get("font_style"):
        state["font_style"] = "Arial"

    return state


def hook_node(state: AgentState):
    """
    Generates and selects the best hook.
    """
    print("--- Hook Agent: Generating hooks ---")
    prompt = HOOK_GENERATION_PROMPT.format(topic=state["topic"], tone=state["tone"])

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()

    # Basic cleaning to ensure JSON parsing
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    try:
        hooks_data = json.loads(content)
        # Sort by score descending
        hooks_data.sort(key=lambda x: x["score"], reverse=True)
        selected_hook = hooks_data[0]["text"]

        state["generated_hooks"] = [h["text"] for h in hooks_data]
        state["selected_hook"] = selected_hook

        # Initialize slides list with the hook slide
        state["slides"] = [
            {
                "slide_number": 1,
                "type": "hook",
                "text": selected_hook,
                "image_path": "",  # To be filled by Designer
                "visual_notes": "",
            }
        ]

    except Exception as e:
        print(f"Error parsing hooks: {e}")
        # Fallback
        state["selected_hook"] = f"Top 5 facts about {state['topic']}"
        state["slides"] = [
            {
                "slide_number": 1,
                "type": "hook",
                "text": state["selected_hook"],
                "image_path": "",
            }
        ]

    return state


def strategist_node(state: AgentState):
    """
    Generates content for the remaining slides.
    """
    print("--- Content Strategist: Writing content ---")
    prompt = CONTENT_GENERATION_PROMPT.format(
        topic=state["topic"],
        tone=state["tone"],
        hook=state["selected_hook"],
        slide_count=state["slide_count"],
        last_minus_1=state["slide_count"] - 1,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()

    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    try:
        texts = json.loads(content)

        # Add generated slides to state
        current_slides = state["slides"]
        for i, text in enumerate(texts):
            slide_num = i + 2  # Start from slide 2
            slide_type = "cta" if slide_num == state["slide_count"] else "content"

            current_slides.append(
                {
                    "slide_number": slide_num,
                    "type": slide_type,
                    "text": text,
                    "image_path": "",
                    "visual_notes": "",
                }
            )

        state["slides"] = current_slides

    except Exception as e:
        print(f"Error parsing content: {e}")

    return state


def designer_node(state: AgentState):
    """
    Selects images and renders slides.
    Raises an error if images cannot be found, so the agent can report back to the orchestrator.
    """
    print("--- Visual Designer: Creating visuals ---")
    images_metadata = json.dumps(image_tool.images, indent=2)

    updated_slides = []
    generated_files = []

    for slide in state["slides"]:
        # 1. Select Image
        prompt = IMAGE_SELECTION_PROMPT.format(
            text=slide["text"], images_metadata=images_metadata
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        image_id = response.content.strip()

        # Clean up ID if needed
        if '"' in image_id:
            image_id = image_id.replace('"', "")

        selected_image = image_tool.get_image_by_id(image_id)

        # 2. Resolve image path
        if not selected_image:
            raise ValueError(
                f"VISUAL_DESIGNER_ERROR: Could not find image with ID '{image_id}' in the image library. "
                f"Please check the image selection. Available images have IDs: {[img.get('id') for img in image_tool.images]}"
            )

        # Resolve virtual path to absolute path
        raw_image_path = selected_image.get("absolute_path", "")
        resolved_image_path = _resolve_image_path(raw_image_path, image_tool)

        # 3. Validate image exists on disk (not URL)
        if not resolved_image_path.startswith(
            "http://"
        ) and not resolved_image_path.startswith("https://"):
            is_valid, error_msg = _validate_image_exists(resolved_image_path)
            if not is_valid:
                raise ValueError(
                    f"VISUAL_DESIGNER_ERROR: {error_msg} "
                    f"Selected image ID '{image_id}' resolved to path '{resolved_image_path}'. "
                    f"Please verify the image library directory structure and ensure images exist at the expected paths."
                )

        slide["image_path"] = resolved_image_path
        slide["visual_notes"] = selected_image.get("description", "")

        # 4. Render Slide
        output_path = renderer_tool.render_slide(slide, state)

        # 5. Validate rendered output is not black
        if output_path.startswith("Error:"):
            raise ValueError(
                f"VISUAL_DESIGNER_ERROR: Failed to render slide {slide['slide_number']}: {output_path}"
            )
        elif os.path.exists(output_path):
            # Check if rendered image is valid (not all black)
            if _is_black_image(output_path, threshold=0.9):
                raise ValueError(
                    f"VISUAL_DESIGNER_ERROR: Rendered slide {slide['slide_number']} is completely black. "
                    f"Image path was '{resolved_image_path}'. "
                    f"Please check if the source image is valid and not corrupted."
                )

        generated_files.append(output_path)

        updated_slides.append(slide)

    state["slides"] = updated_slides
    state["files_to_upload"] = generated_files

    return state


def publisher_node(state: AgentState):
    """
    Uploads to Drive and saves to Knowledge Base.
    """
    print("--- Publisher: Uploading and Archiving ---")

    # 1. Create Folder
    folder_name = f"{state['project_id']}_{state['topic'].replace(' ', '_')}"
    folder_id = drive_tool.create_folder(folder_name)

    # 2. Upload Files
    files = state.get("files_to_upload", [])
    drive_link = drive_tool.upload_files(files, folder_id)
    state["drive_folder_link"] = drive_link

    # 3. Save to KB
    kb_tool.save_slideshow(
        project_id=state["project_id"],
        topic=state["topic"],
        slides=state["slides"],
        drive_link=drive_link,
    )

    return state
