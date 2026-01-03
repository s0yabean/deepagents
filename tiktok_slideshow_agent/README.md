# TikTok Slideshow Agent - Product Spec

## 🚀 Quickstart

Run the local LangGraph Studio:

```bash
langgraph dev
```

## 1. Vision
To build an automated, intelligent agent capable of generating high-quality, engaging TikTok slideshows (images with text overlays) daily. The agent learns from past performance, adapts to different project requirements, and seamlessly integrates with the user's workflow by delivering final assets to Google Drive.

## 2. User Stories
- **Daily Generation**: As a creator, I want to trigger the agent with a simple command or topic so that I can get a fresh batch of slideshows ready for posting every day.
- **Customization**: As a creator, I want to define different "Projects" (e.g., "Motivation", "Business Tips") with specific rules (e.g., 3 slides vs. 6 slides) so the content fits the niche.
- **Visual Consistency**: As a brand owner, I want all images to use a standard TikTok font and 9:16 ratio so that my feed looks professional and native to the platform.
- **Hook Optimization**: As a creator, I want a specialized agent to brainstorm and score multiple hooks for the first slide, ensuring maximum viewer retention.
- **Asset Management**: As a user, I want the final images to be saved in a specific Google Drive folder, organized by date and project, so I have a reliable archive.

## 3. System Architecture

### 3.1 Agents
The system will use a multi-agent architecture orchestrated by a main supervisor.

1.  **Orchestrator Agent**:
    -   **Role**: The project manager. Receives user specs, fetches rules, and coordinates the workflow.
    -   **Responsibilities**: Parse user input, load project config, delegate to Hook Agent then Content Strategist.

2.  **Hook Agent** (New):
    -   **Role**: The viral specialist.
    -   **Responsibilities**:
        -   Focus exclusively on Slide 1.
        -   Generate multiple hook variations based on the topic.
        -   Score hooks (internal logic or LLM evaluation) and select the best one.

3.  **Content Strategist Agent**:
    -   **Role**: The copywriter.
    -   **Responsibilities**:
        -   Take the winning hook and write the remaining slides (Value -> CTA).
        -   Ensure the narrative flow works for the specific slide count (e.g., 3, 5, or 6 slides).

4.  **Visual Designer Agent**:
    -   **Role**: The graphic designer.
    -   **Responsibilities**:
        -   Select appropriate images from the `ImageLibrary` for *each* slide.
        -   Map text to images.
        -   Generate HTML/CSS for the overlay (using standard TikTok fonts).
        -   Use Playwright to render and screenshot the final 9:16 images.

5.  **Publisher Agent**:
    -   **Role**: The archiver.
    -   **Responsibilities**:
        -   Upload generated images to Google Drive.
        -   Log the full details to `slideshows.json`.

### 3.2 Tools
-   **`ImageLibraryTool`**: Scans local directory for images.
-   **`PlaywrightRendererTool`**: Renders HTML/CSS to 9:16 PNGs.
-   **`GoogleDriveTool`**: Uploads files to Drive.
-   **`KnowledgeBaseTool`**: Reads/Writes to `slideshows.json`.

## 4. Configuration & Rules

### Project Definitions
*Example Config:*
```json
{
  "project_id": "motivation_daily",
  "slide_count": 5,
  "tone": "Inspirational",
  "font_style": "Proxima Nova (TikTok Standard)",
  "cta_type": "Follow for more"
}
```

## 5. Workflow
1.  **Trigger**: User runs `python run_agent.py --project motivation --topic "Discipline"`.
2.  **Planning**: Orchestrator loads "motivation" config (5 slides).
3.  **Hook Generation**: Hook Agent generates 5 hooks, scores them, picks "Why you will regret not starting today".
4.  **Content**: Strategist writes slides 2-5 based on the hook.
5.  **Visuals**: Designer picks 5 unique images, overlays text, renders.
6.  **Delivery**: Publisher uploads to Drive.
7.  **Learning**: Publisher appends full run details to `slideshows.json`.

## 6. Technical Stack
-   **Framework**: LangGraph.
-   **LLM**: Gemini 1.5 Pro.
-   **Browser**: Playwright (Chromium).
-   **Storage**: Local FS + Google Drive API.

## 7. Configuration

To run this agent, you need to set up the following in your `.env` file:

```bash
# Required
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=... # If using Claude
TAVILY_API_KEY=...    # For Hook Agent research

# Google Drive & Gmail (Optional but recommended)
# Follow LangChain Google Community setup instructions
GOOGLE_APPLICATION_CREDENTIALS=credentials.json 
```

### Human-in-the-Loop
To enable manual review before publishing, add this to your `.env` file:
`ENABLE_HUMAN_REVIEW=True` 

If set to `True`, the agent will pause before the `publisher` step to allow you to review the generated artifacts.
