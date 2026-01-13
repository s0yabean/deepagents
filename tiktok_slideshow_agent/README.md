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
# Required - LLM
GOOGLE_API_KEY=...          # Gemini API key
TAVILY_API_KEY=...          # For Hook Agent research

# Google Drive (OAuth - Personal Account)
# 1. Create OAuth credentials in Google Cloud Console
# 2. Download credentials.json and save in project root
# 3. Run agent locally once to authenticate (creates token.json)
# 4. Create a folder in your Drive and get its ID
GOOGLE_DRIVE_PARENT_ID=...  # ID of your Drive folder (from URL)

# Email (SMTP with App Password)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Generate at myaccount.google.com/apppasswords
SMTP_FROM=your-email@gmail.com
EMAIL_TO=recipient@gmail.com     # Default notification recipient
```

### Google Drive Setup (OAuth - Personal Account)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the **Google Drive API** in your project
4. Go to **APIs & Services → Credentials**
5. Click **Create Credentials → OAuth 2.0 Client ID**
6. Choose **Desktop app** as application type
7. Download the credentials JSON file
8. Rename to `credentials.json` and place in project root
9. Run the agent locally - browser will open for authentication
10. After authentication, `token.json` will be created automatically
11. Create a folder in your Google Drive and copy its ID from the URL

### Email Setup (SMTP)
1. Enable 2-Step Verification on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Create a new app password for "Mail"
4. Use this password as `SMTP_PASSWORD`

### Human-in-the-Loop
To enable manual review before publishing, add this to your `.env` file:
`ENABLE_HUMAN_REVIEW=True`

If set to `True`, the agent will pause before the `publisher` step to allow you to review the generated artifacts.

## 8. VPS/Docker Deployment

### Required Files NOT in Git
The following files contain secrets and are **NOT** committed to git. You must transfer them to your VPS manually:

#### **1. Credential Files (3 files):**
- `credentials.json` - OAuth client credentials for Google APIs
- `token.json` - Google Drive API token (auto-refreshes)
- `token_gmail.json` - Gmail API token (if using email features)

#### **2. Environment File:**
- `.env` - Contains all API keys and configuration

### Deployment Steps

1. **Clone repository on VPS:**
   ```bash
   git clone <your-repo-url>
   cd tiktok_slideshow_agent
   ```

2. **Transfer credential files from local machine:**
   ```bash
   # From your local machine (not on VPS)
   scp tiktok_slideshow_agent/credentials.json user@your-vps:/path/to/tiktok_slideshow_agent/
   scp tiktok_slideshow_agent/token.json user@your-vps:/path/to/tiktok_slideshow_agent/
   scp tiktok_slideshow_agent/token_gmail.json user@your-vps:/path/to/tiktok_slideshow_agent/
   scp tiktok_slideshow_agent/.env user@your-vps:/path/to/tiktok_slideshow_agent/
   ```

3. **Secure file permissions on VPS:**
   ```bash
   # SSH into your VPS
   ssh user@your-vps

   # Set secure permissions (only your user can read)
   cd /path/to/tiktok_slideshow_agent
   chmod 600 credentials.json token.json token_gmail.json .env
   ```

4. **Build and run Docker container:**
   ```bash
   docker build -t tiktok-slideshow-agent .
   docker run -d \
     --name tiktok-agent \
     -v $(pwd)/credentials.json:/app/credentials.json:ro \
     -v $(pwd)/token.json:/app/token.json:ro \
     -v $(pwd)/token_gmail.json:/app/token_gmail.json:ro \
     -v $(pwd)/.env:/app/.env:ro \
     tiktok-slideshow-agent
   ```

### Initial Authentication (Run Locally Before Deploying)

Before deploying to VPS, you **MUST** authenticate locally to generate token files. This opens a browser for you to log in with your Google account.

#### **Authenticate for Google Drive (`token.json`):**

Create and run this test script:
```python
# test_drive_auth.py
import asyncio
from tiktok_slideshow_agent.tools.drive import GoogleDriveTool

async def test_auth():
    print("Testing Google Drive authentication...")
    print("A browser window will open - please log in and grant permissions.")

    drive = GoogleDriveTool()
    await drive._ensure_service()

    print("\n✅ Authentication successful!")
    print("token.json has been created.")

if __name__ == "__main__":
    asyncio.run(test_auth())
```

Run it:
```bash
python test_drive_auth.py
```

#### **Authenticate for Gmail (`token_gmail.json`):**

If you're using Gmail/email features, you need to authenticate for Gmail separately. Check your existing email/Gmail integration code and run it once locally to trigger OAuth and create `token_gmail.json`.

Alternatively, just run your full agent locally once:
```bash
langgraph dev
# Then trigger a workflow that uses Google Drive or Gmail
```

The browser will open automatically during first use, and the token files will be saved.

### Important Notes

- **Token Refresh**: `token.json` will auto-refresh programmatically on VPS (no browser needed)
- **Initial Auth**: You MUST authenticate locally first to generate token files before deploying
- **Security**: Never commit credential files to git
- **Backup**: Keep local copies of all credential files in a secure location
