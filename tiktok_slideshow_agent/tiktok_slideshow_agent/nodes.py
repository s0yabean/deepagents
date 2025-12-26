import json
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage
from .state import AgentState, Slide
from .prompts import HOOK_GENERATION_PROMPT, CONTENT_GENERATION_PROMPT, IMAGE_SELECTION_PROMPT
from .tools import ImageLibraryTool, PlaywrightRendererTool, GoogleDriveTool, KnowledgeBaseTool

# Initialize Tools
image_tool = ImageLibraryTool()
renderer_tool = PlaywrightRendererTool()
drive_tool = GoogleDriveTool()
kb_tool = KnowledgeBaseTool()

class MockLLM:
    def invoke(self, messages):
        content = messages[0].content
        if "Hook" in content:
            return type('obj', (object,), {'content': '''
            [
                {"text": "Mock Hook 1: The Secret to Success", "score": 9, "reason": "High curiosity"},
                {"text": "Mock Hook 2: Why you are failing", "score": 8, "reason": "Negative bias"}
            ]
            '''})
        elif "Storyteller" in content:
            return type('obj', (object,), {'content': '''
            [
                "Slide 2: Consistency is key.",
                "Slide 3: Don't give up.",
                "Slide 4: Just do it.",
                "Follow for more."
            ]
            '''})
        elif "visual director" in content:
            # Return a valid ID from images.json
            return type('obj', (object,), {'content': 'motivational_01'})
        return type('obj', (object,), {'content': ''})

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
    prompt = HOOK_GENERATION_PROMPT.format(
        topic=state["topic"],
        tone=state["tone"]
    )
    
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
        state["slides"] = [{
            "slide_number": 1,
            "type": "hook",
            "text": selected_hook,
            "image_path": "", # To be filled by Designer
            "visual_notes": ""
        }]
        
    except Exception as e:
        print(f"Error parsing hooks: {e}")
        # Fallback
        state["selected_hook"] = f"Top 5 facts about {state['topic']}"
        state["slides"] = [{"slide_number": 1, "type": "hook", "text": state["selected_hook"], "image_path": ""}]

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
        last_minus_1=state["slide_count"] - 1
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
            slide_num = i + 2 # Start from slide 2
            slide_type = "cta" if slide_num == state["slide_count"] else "content"
            
            current_slides.append({
                "slide_number": slide_num,
                "type": slide_type,
                "text": text,
                "image_path": "",
                "visual_notes": ""
            })
            
        state["slides"] = current_slides
        
    except Exception as e:
        print(f"Error parsing content: {e}")
        
    return state

def designer_node(state: AgentState):
    """
    Selects images and renders slides.
    """
    print("--- Visual Designer: Creating visuals ---")
    images_metadata = json.dumps(image_tool.images, indent=2)
    
    updated_slides = []
    generated_files = []
    
    for slide in state["slides"]:
        # 1. Select Image
        prompt = IMAGE_SELECTION_PROMPT.format(
            text=slide["text"],
            images_metadata=images_metadata
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        image_id = response.content.strip()
        
        # Clean up ID if needed
        if '"' in image_id:
            image_id = image_id.replace('"', '')
            
        selected_image = image_tool.get_image_by_id(image_id)
        
        # Fallback if ID not found or hallucinated
        if not selected_image:
            print(f"Warning: Image ID {image_id} not found. Using random fallback.")
            selected_image = image_tool.images[0]
            selected_image["absolute_path"] = os.path.join(image_tool.base_path, selected_image["category"], selected_image["filename"])

        slide["image_path"] = selected_image["absolute_path"]
        slide["visual_notes"] = selected_image.get("description", "")
        
        # 2. Render Slide
        output_path = renderer_tool.render_slide(slide, state)
        generated_files.append(output_path)
        
        updated_slides.append(slide)
        
    state["slides"] = updated_slides
    # Store generated file paths in a temporary key or just rely on the fact they are on disk
    # For the publisher, we need the paths.
    # Let's add a list of paths to upload to the state or just re-derive them.
    # Actually, let's just use the output dir logic in Publisher or pass them explicitly.
    # We'll add a temporary field to state for upload
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
        drive_link=drive_link
    )
    
    return state
