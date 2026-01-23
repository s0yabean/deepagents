from langchain_core.tools import tool
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from tiktok_slideshow_agent.tools.images import ImageLibraryTool
from tiktok_slideshow_agent.tools.renderer import PlaywrightRendererTool
from tiktok_slideshow_agent.tools.drive import GoogleDriveTool
from tiktok_slideshow_agent.tools.knowledge import KnowledgeBaseTool
from tiktok_slideshow_agent.tools.sync_tool import sync_image_library
from tiktok_slideshow_agent.tools.pexels_handler import search_pexels_with_fallback

# Ensure .env is loaded before any tools run
load_dotenv()


# Format Library path - relative to project root
def _get_format_library_path():
    current_file = Path(__file__).resolve()
    # tools -> tiktok_slideshow_agent -> PROJECT_ROOT
    base_path = current_file.parent.parent.parent
    return base_path / "format_library.json"


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


async def initialize_google_drive():
    """
    Initialize and validate Google Drive token on startup (NON-BLOCKING).
    This should be called BEFORE the agent starts processing tasks.

    This will:
    1. Fetch the token from GitHub private repo
    2. Check if it expires within 40 minutes
    3. If expiring, trigger GitHub Actions workflow to refresh (in background)
    4. Return IMMEDIATELY without waiting (agent can start working)
    5. Refresh verification happens later when Drive is actually needed (~10 min)

    Benefits:
    - Agent starts instantly (no 30-60s startup delay)
    - Refresh happens in background during agent work
    - By the time publisher runs, token is usually already refreshed

    Raises:
        ValueError: If required environment variables are missing
        Exception: For network/authentication errors during token fetch
    """
    drive_tool = get_drive()
    return await drive_tool.validate_token_async()


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
async def render_slide(
    text: str, image_path: str, slide_number: int, output_dir: str = None
) -> str:
    """Render a slide with text and image, returning the output path.

    Args:
        text: The overlay text for the slide.
        image_path: The background image path (local absolute path OR Pexels URL).
                   URLs will be automatically downloaded during rendering.
        slide_number: The sequence number of the slide.
        output_dir: Optional absolute path to the directory where the slide should be saved.
    """
    slide_data = {"text": text, "image_path": image_path, "slide_number": slide_number}
    # Config can be expanded later
    config = {"font_style": "Montserrat"}

    # Run async renderer
    return await get_renderer().render_slide(slide_data, config, output_dir=output_dir)


@tool
async def setup_project_folder(topic: str) -> dict:
    """Creates a timestamped project folder locally AND on Google Drive.

    Called ONLY by Publisher at the start of rendering.

    Returns:
        A dictionary containing paths and IDs:
        - project_root_id: ID of the root folder on Drive.
        - local_project_root: Absolute local path to the project root.
        - local_slideshows_dir: Absolute local path for rendered images.
        - local_metadata_dir: Absolute local path for metadata.
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

    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp = now.strftime("%d%m%Y_%H%M")

    # Increase descriptiveness: Fix regex to allow all numbers, max 3 words, max 30 chars
    # Remove special chars (keep letters, numbers, spaces)
    clean_topic = re.sub(r"[^a-zA-Z0-9\s]", "", topic)

    # Split into words, take max 3, join with underscore
    words = clean_topic.split()
    short_topic = "_".join(words[:3])

    reel_name = short_topic.lower().strip()
    reel_name = reel_name[:30]

    root_folder_name = f"{timestamp}_UTC_sayura_{reel_name}"

    # 1. Local Creation (will reuse if already created by save_locally)
    local_project_root = output_base / root_folder_name
    local_slideshows_dir = local_project_root / "slideshows"
    local_metadata_dir = local_project_root / "metadata"

    await asyncio.to_thread(os.makedirs, local_project_root, exist_ok=True)
    await asyncio.to_thread(os.makedirs, local_slideshows_dir, exist_ok=True)
    await asyncio.to_thread(os.makedirs, local_metadata_dir, exist_ok=True)

    # 2. Drive Creation (Target Folder ID specified by user)
    # Target ID: Configured in .env (GOOGLE_DRIVE_PARENT_ID)
    TARGET_DRIVE_PARENT_ID = os.getenv("GOOGLE_DRIVE_PARENT_ID")
    if not TARGET_DRIVE_PARENT_ID:
        return {"error": "GOOGLE_DRIVE_PARENT_ID not set in .env"}

    # Create subfolder using personal OAuth account
    root_folder_id = await get_drive().create_folder(
        root_folder_name, parent_id=TARGET_DRIVE_PARENT_ID
    )

    return {
        "project_root_id": root_folder_id,
        "local_project_root": str(local_project_root),
        "local_slideshows_dir": str(local_slideshows_dir),
        "local_metadata_dir": str(local_metadata_dir),
        "folder_name": root_folder_name,
    }


@tool
async def save_locally(project_id: str, topic: str, slides: str) -> str:
    """Save metadata locally and record in the Knowledge Base.

    Auto-creates the project folder structure based on topic and timestamp.

    Args:
        project_id: Unique identifier for the project.
        topic: The main topic of the slideshow.
        slides: A JSON string representing a list of slide objects.
    """
    import datetime
    import re
    from pathlib import Path

    try:
        if isinstance(slides, list):
            slides_data = slides
        else:
            slides_data = json.loads(slides)
    except json.JSONDecodeError:
        return "Error: 'slides' argument must be a valid JSON string representing a list of slides."

    # 1. Construct metadata directory path (same logic as setup_project_folder)
    current_file = Path(__file__).resolve()
    base_path = current_file.parent.parent.parent
    output_base = base_path / "output"

    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp = now.strftime("%d%m%Y_%H%M")

    clean_topic = re.sub(r"[^a-zA-Z0-9\s]", "", topic)
    words = clean_topic.split()
    short_topic = "_".join(words[:3])
    reel_name = short_topic.lower().strip()[:30]

    root_folder_name = f"{timestamp}_UTC_sayura_{reel_name}"
    local_project_root = output_base / root_folder_name
    local_metadata_dir = local_project_root / "metadata"

    # Create metadata directory
    await asyncio.to_thread(os.makedirs, local_metadata_dir, exist_ok=True)

    # Save metadata.json
    metadata_path = local_metadata_dir / "metadata.json"

    def save_metadata_sync():
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(slides_data, f, indent=4)

    await asyncio.to_thread(save_metadata_sync)

    # 2. Save to KB (historical record)
    await asyncio.to_thread(
        get_kb().save_slideshow, project_id, topic, slides_data, "Drive Upload"
    )

    return f"Metadata recorded in Knowledge Base and saved to {local_metadata_dir}"


@tool
async def read_metadata_file(metadata_dir: str) -> str:
    """Read the approved metadata.json file from disk.

    This is the source of truth for rendering - it contains the exact approved slides.

    Args:
        metadata_dir: The directory containing metadata.json (from setup_project_folder).

    Returns:
        A JSON string containing the approved slide list, or an error message.
    """
    metadata_path = os.path.join(metadata_dir, "metadata.json")

    def read_file_sync():
        if not os.path.exists(metadata_path):
            return None
        with open(metadata_path, "r", encoding="utf-8") as f:
            return f.read()

    content = await asyncio.to_thread(read_file_sync)

    if content is None:
        return f"Error: metadata.json not found at {metadata_path}. QA Specialist must approve and save metadata first."

    return content


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
async def send_email_notification(
    subject: str, content: str, to_email: str = None
) -> str:
    """Sends an email notification via SMTP.

    **IMPORTANT**: You do NOT need to provide a recipient email.
    The system automatically sends to the admin email (EMAIL_TO from .env).

    Args:
        subject: The email subject line.
        content: The body text of the email (include Drive link here).
        to_email: ONLY provide this if user explicitly requested an additional recipient.
                  Leave empty for normal operations - admin will receive it automatically.

    Example usage:
        send_email_notification(
            subject="New Slideshow Generated",
            content="Your slideshow is ready: https://drive.google.com/..."
        )

    Returns:
        Success message with recipient info, or error message if EMAIL_TO not configured.
    """
    recipients = []

    # 1. Always include the admin email from .env
    env_email = os.getenv("EMAIL_TO")
    if not env_email:
        return "❌ ERROR: EMAIL_TO not configured in .env file. Cannot send notification. Please add EMAIL_TO=your-email@gmail.com to your .env file."

    recipients.append(env_email)

    # 2. Include agent-specified email if provided and different
    if to_email and to_email.strip() and to_email != env_email:
        recipients.append(to_email)

    if not recipients:
        return "Error: No recipient email provided in .env or arguments."

    # Send to all recipients
    results = []
    for recipient in recipients:
        try:
            # We treat subject slightly differently to avoid threading issues if desired,
            # but usually same subject is fine.
            res = await get_drive().send_email(recipient, subject, content)
            results.append(f"Sent to {recipient}: {res}")
        except Exception as e:
            results.append(f"Failed to send to {recipient}: {str(e)}")

    return "\n".join(results)


@tool
def request_human_approval(summary: str) -> str:
    """Request human approval for the current plan or content.

    This tool triggers a system interrupt. Execution will pause until the human approves.
    If ENABLE_HUMAN_REVIEW=false in .env, this tool auto-approves without pausing.

    Args:
        summary: A brief summary of what is being approved (e.g., "QA Approved: Script and Images look good").
    """
    # Check if human review is enabled
    enable_human_review = os.getenv("ENABLE_HUMAN_REVIEW", "True").lower() == "true"

    if not enable_human_review:
        # Auto-approve without interrupting
        return f"Auto-approved (ENABLE_HUMAN_REVIEW=false): {summary}"

    from langgraph.types import interrupt

    # This pauses execution. The value passed to interrupt() is shown to the user/client.
    # The value returned by interrupt() is what the user provides when resuming (or None).
    user_feedback = interrupt(summary)

    if user_feedback and isinstance(user_feedback, str):
        return f"Human Feedback: {user_feedback}"

    return "Human approved"


@tool
def read_format_library() -> str:
    """Read the Format Library containing proven TikTok slideshow formats.

    Returns the full format library JSON with:
    - formats: List of proven formats (transformation-story, myth-busting, listicle, etc.)
    - hook_formulas: Universal hook templates
    - cta_styles: Call-to-action approaches
    - product_positioning_guide: How to position products
    - universal_principles: Key rules for viral content

    The Creative Director should ALWAYS read this before creating a Creative Brief.
    """
    format_lib_path = _get_format_library_path()

    if not format_lib_path.exists():
        return json.dumps({"error": f"Format library not found at {format_lib_path}"})

    with open(format_lib_path, "r", encoding="utf-8") as f:
        return f.read()


@tool
async def verify_drive_upload(folder_id: str, expected_slide_count: int) -> str:
    """Verifies that all required files were uploaded to Google Drive.

    This tool performs a critical verification step after upload to ensure:
    1. metadata.json exists in the Drive folder
    2. All expected slide images were uploaded

    CRITICAL: This tool MUST be called after upload_to_drive and BEFORE send_email_notification.

    Args:
        folder_id: The Google Drive folder ID where files were uploaded.
        expected_slide_count: The number of slide images that should be present.

    Returns:
        Success message if all files present, or detailed error message listing missing files.
    """
    # List all files in the Drive folder
    files_in_folder = await get_drive().list_folder_files(folder_id)

    # Check for metadata.json
    has_metadata = "metadata.json" in files_in_folder

    # Count slide images (files ending with .png or .jpg)
    slide_images = [
        f for f in files_in_folder if f.endswith(".png") or f.endswith(".jpg")
    ]
    actual_slide_count = len(slide_images)

    # Build verification report
    issues = []

    if not has_metadata:
        issues.append("❌ CRITICAL: metadata.json is MISSING from Drive folder")

    if actual_slide_count != expected_slide_count:
        issues.append(
            f"❌ CRITICAL: Expected {expected_slide_count} slides, but found {actual_slide_count} in Drive folder"
        )

    if issues:
        error_report = "\n".join(issues)
        error_report += f"\n\nFiles found in folder: {', '.join(files_in_folder)}"
        return f"VERIFICATION FAILED:\n{error_report}"

    # All checks passed
    return f"✅ VERIFICATION PASSED: All {expected_slide_count} slides + metadata.json confirmed in Drive folder (Total: {len(files_in_folder)} files)"


@tool
def get_brief_fields(brief_id: str, fields: list[str]) -> str:
    """Retrieve specific fields from the Creative Brief stored in agent state.

    This tool enables context-efficient access to Creative Brief data.
    Instead of receiving the full 2000+ character brief JSON, agents can request
    only the fields they need.

    Args:
        brief_id: The Creative Brief identifier (e.g., "brief_20260123_abc123").
        fields: List of field names to retrieve from the brief.
               Common fields by agent:
               - hook-agent: ["hooks", "tone", "target_audience", "hook_style", "reference_hooks", "avoid"]
               - content-strategist: ["narrative_arc", "product_position", "product_mention_guidance", "cta_style", "cta_examples", "avoid"]
               - visual-designer: ["image_arc", "tone", "format_id"]
               - qa-specialist: ["slides", "format_id", "tone", "hook_style", "narrative_arc", "product_position", "image_arc", "cta_style"]

    Returns:
        A JSON string containing only the requested fields from the Creative Brief.
        Returns error message if brief_id not found or fields not in brief.

    Example:
        get_brief_fields("brief_20260123_abc123", ["tone", "image_arc"])
        Returns: {"tone": "energetic", "image_arc": ["moody", "moody", "transitional", "bright", "bright"]}
    """
    import json

    # This tool requires access to agent state. In LangGraph, state is passed via context.
    # For now, return instructions for how this integrates with state.
    # The actual implementation will read from state['creative_brief'] where brief_id matches.

    # Placeholder for state integration - actual access happens via state context
    return json.dumps(
        {
            "brief_id": brief_id,
            "requested_fields": fields,
            "status": "brief_access_tool_available",
            "note": "This tool accesses state['creative_brief'] in the actual implementation",
            "expected_fields": fields,
        }
    )
