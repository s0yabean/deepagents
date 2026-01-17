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

# Google Drive (OAuth - Automated Token Management)
# Token is fetched from private GitHub repository and auto-refreshed
GOOGLE_DRIVE_PARENT_ID=...  # ID of your Drive folder (from URL)

# GitHub Token Access (for fetching OAuth tokens from private repo)
GITHUB_TOKEN=ghp_your_personal_access_token_here  # Needs 'repo' + 'workflow' scopes
GOOGLE_OAUTH_TOKEN_REPO_URL=https://raw.githubusercontent.com/s0yabean/lambda_jobs/secrets/token.json

# GitHub Actions Workflow Trigger (for automatic token refresh)
GITHUB_REPO_OWNER=s0yabean
GITHUB_REPO_NAME=lambda_jobs
GITHUB_WORKFLOW_FILE=refresh_google_token.yml
GITHUB_DEFAULT_BRANCH=master  # or "main"

# Token Refresh Settings (optional - defaults shown)
TOKEN_EXPIRY_THRESHOLD_MINUTES=40  # Refresh if expiring within 40 mins
TOKEN_REFRESH_POLL_TIMEOUT=30  # Max seconds to wait for workflow

# Email (SMTP with App Password)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Generate at myaccount.google.com/apppasswords
SMTP_FROM=your-email@gmail.com
EMAIL_TO=recipient@gmail.com     # Default notification recipient
```

### Google Drive Setup (Automated Token Management)

**New Approach:** OAuth tokens are managed automatically via GitHub repository and GitHub Actions workflows. No manual browser authentication required!

#### Prerequisites
1. A GitHub Personal Access Token with `repo` + `workflow` scopes
   - Go to https://github.com/settings/tokens/new
   - Name: "TikTok Agent Drive Access"
   - Scopes: Select `repo` (full) and `workflow`
   - Click "Generate token" and save it securely

2. A private GitHub repository storing your OAuth token (e.g., `lambda_jobs`)
   - The token should be stored at a path like `/secrets/token.json`
   - A GitHub Actions workflow (`refresh_google_token.yml`) should handle token refresh

3. A Google Drive folder for output
   - Create a folder in your Google Drive
   - Copy its ID from the URL (e.g., `1A2B3C4D5E6F7G8H9I0J`)

#### Configuration
1. Add all required variables to `.env` (see Configuration section above)
2. The agent will automatically:
   - Fetch the token from your private GitHub repo on startup
   - Check if the token expires within 40 minutes
   - Trigger a GitHub Actions workflow to refresh if needed
   - Poll and wait for the refresh to complete
   - Proceed only when a valid token is confirmed

#### Usage in Code
```python
from tiktok_slideshow_agent.tools.agent_tools import initialize_google_drive

# Call this BEFORE starting the agent
await initialize_google_drive()
```

This prevents authentication failures mid-workflow!

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

#### **Environment File:**
- `.env` - Contains all API keys and configuration (including `GITHUB_TOKEN`)

### Deployment Steps

1. **Clone repository on VPS:**
   ```bash
   git clone <your-repo-url>
   cd tiktok_slideshow_agent
   ```

2. **Transfer environment file from local machine:**
   ```bash
   # From your local machine (not on VPS)
   scp tiktok_slideshow_agent/.env user@your-vps:/path/to/tiktok_slideshow_agent/
   ```

3. **Secure file permissions on VPS:**
   ```bash
   # SSH into your VPS
   ssh user@your-vps

   # Set secure permissions (only your user can read)
   cd /path/to/tiktok_slideshow_agent
   chmod 600 .env
   ```

4. **Build and run Docker container:**
   ```bash
   docker build -t tiktok-slideshow-agent .
   docker run -d \
     --name tiktok-agent \
     -v $(pwd)/.env:/app/.env:ro \
     tiktok-slideshow-agent
   ```

**Note:** OAuth tokens are now fetched automatically from your private GitHub repository - no need to transfer credential files!

### Token Validation on Startup

The agent automatically validates and refreshes tokens on startup. To test this locally:

```python
# test_token_validation.py
import asyncio
from tiktok_slideshow_agent.tools.agent_tools import initialize_google_drive

async def test_validation():
    print("Testing token validation and refresh...")

    token_data = await initialize_google_drive()

    print("\n✅ Token validation successful!")
    print(f"Token expires at: {token_data.get('expiry')}")

if __name__ == "__main__":
    asyncio.run(test_validation())
```

Run it:
```bash
python test_token_validation.py
```

### Important Notes

- **Automated Refresh**: Tokens are automatically fetched from GitHub and refreshed via GitHub Actions
- **No Browser Auth**: No browser authentication needed - everything is automated
- **40-Min Threshold**: Token is refreshed automatically if expiring within 40 minutes
- **GitHub Actions**: Your `refresh_google_token.yml` workflow must be properly configured
- **Security**: Keep your `GITHUB_TOKEN` secure and never commit it to git
