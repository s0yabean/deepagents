# TikTok Slideshow Agent - Multi-Agent Content Creation System

## 🚀 Quickstart

Run the local LangGraph Studio:

```bash
cd tiktok_slideshow_agent
langgraph dev
```

## Overview

An AI-powered multi-agent system that creates viral TikTok slideshows using a **"Creative Director First"** workflow. The system mimics a high-end creative agency with specialized agents for strategy, content creation, visual design, and quality control.

### Key Features

- **Strategy-First**: Creative Brief guides all downstream agents
- **Skills-Based Architecture**: Context-efficient brief management via `brief_id`
- **Double Verification**: Orchestrator independently verifies Drive uploads
- **Pexels Integration**: Auto-fallback image search with Single Protagonist Rule
- **Google Drive Delivery**: Automated upload with folder organization
- **Email Notifications**: Completion alerts sent after Orchestrator verification

## Agent Team

| Agent | Role | Key Tools |
|-------|------|-----------|
| **Orchestrator** | Executive Producer | `verify_drive_upload`, `send_email_notification` |
| **Creative Director** | Strategy Lead | `read_format_library`, `TavilySearch` |
| **Hook Agent** | Viral Specialist | `TavilySearch`, `get_brief_fields` |
| **Content Strategist** | Scriptwriter | `get_brief_fields` |
| **Visual Designer** | Art Director | `sync_image_library`, `search_pexels_with_fallback`, `verify_visual_consistency` |
| **QA Specialist** | Quality Control | `request_human_approval`, `save_locally` |
| **Publisher** | Delivery | `setup_project_folder`, `render_slide`, `upload_to_drive` |

## Workflow

```
User Input → Orchestrator
    ↓
Creative Director → Creates Creative Brief (stored in state with brief_id)
    ↓
Hook → Content → Visual → QA (with human review if enabled)
    ↓
Publisher: Render → Upload (slides + metadata.json in ONE call)
    ↓
Orchestrator: Double-verify → Send Email → Report to User
```

## Skills System

The agent uses skills for context-efficient operations:

| Skill | Purpose |
|-------|---------|
| `creative-brief-manager` | Stores briefs in state, provides `get_brief_fields()` |
| `visual-designer-skill` | Image selection and Pexels integration |
| `publisher-skill` | Rendering and upload workflows |
| `orchestrator-workflow` | Agent coordination and verification |

### Context-Efficient Brief Pattern

**Old (bloated):**
```python
task(agent="hook", task="Generate hooks. Brief: {...2000 chars...}")
```

**New (efficient):**
```python
task(agent="hook", task="Generate hooks. brief_id: brief_20260123_abc123")
# Agent calls:
get_brief_fields("brief_20260123_abc123", ["hooks", "tone"])
# Returns only needed fields (~200 chars vs ~2000)
```

## 2-Step Verification

### Step 1: Publisher
1. Upload ALL files in ONE call: slides + metadata.json
2. Verify upload
3. Return `folder_name`, `folder_id`, `drive_link` to Orchestrator

### Step 2: Orchestrator (Double-Check)
1. Call `verify_drive_upload(folder_id, expected_count)`
2. Checks:
   - `metadata.json` exists at root
   - `slide_1.png` through `slide_N.png` all present
   - No missing/duplicate slides
3. If PASS: Send email and report to user
4. If FAIL: Send back to Publisher for retry

## File Structure

```
tiktok_slideshow_agent/
├── agent.py                    # Main entry, agent/subagent definitions
├── state.py                    # AgentState schema
├── tiktok_slideshow_agent/
│   ├── tools/
│   │   ├── agent_tools.py      # Core tools (render, upload, verify, email)
│   │   ├── drive.py            # Google Drive integration
│   │   ├── pexels_handler.py   # Pexels API with fallback
│   │   └── renderer.py         # Playwright rendering
│   ├── prompts/
│   │   ├── orchestrator.py     # Orchestrator instructions
│   │   └── specialists.py      # All specialist prompts
│   ├── skills/                 # Skill implementations
│   └── fonts/                  # Font files
├── skills/                     # Skills directory
│   ├── creative-brief-manager/
│   │   └── scripts/            # brief_manager.py, validate_brief.py
│   ├── visual-designer-skill/
│   ├── publisher-skill/
│   └── ...
├── docs/
│   └── system_architecture.md  # Detailed architecture docs
├── format_library.json         # Proven viral formats
├── knowledge_base.json         # Historical record
└── output/                     # Generated slideshows
```

## Configuration

See [Configuration Section](#configuration) below for `.env` setup.
To build an automated, intelligent agent capable of generating high-quality, engaging TikTok slideshows (images with text overlays) daily. The agent learns from past performance, adapts to different project requirements, and seamlessly integrates with the user's workflow by delivering final assets to Google Drive.

## 2. User Stories
- **Daily Generation**: As a creator, I want to trigger the agent with a simple command or topic so that I can get a fresh batch of slideshows ready for posting every day.
- **Customization**: As a creator, I want to define different "Projects" (e.g., "Motivation", "Business Tips") with specific rules (e.g., 3 slides vs. 6 slides) so the content fits the niche.
- **Visual Consistency**: As a brand owner, I want all images to use a standard TikTok font and 9:16 ratio so that my feed looks professional and native to the platform.
- **Hook Optimization**: As a creator, I want a specialized agent to brainstorm and score multiple hooks for the first slide, ensuring maximum viewer retention.
- **Asset Management**: As a user, I want the final images to be saved in a specific Google Drive folder, organized by date and project, so I have a reliable archive.

## System Architecture

### 3.1 Agents

The system uses a multi-agent architecture with a **Creative Director First** workflow.

**Orchestrator (NEW - Main Supervisor):**
- Role: Executive Producer
- Responsibilities: Coordinates all agents, performs 2-step Drive verification, sends email notifications
- **Key Change**: Now handles email (after verification) instead of Publisher

**Creative Director (NEW - Runs First):**
- Role: Top-level strategist
- Responsibilities: Analyzes product/topic, reads format_library.json, creates Creative Brief
- Key Output: `brief_id` for downstream agents (context-efficient pattern)

**Hook Agent:**
- Role: Viral specialist
- Responsibilities: Generates hooks matching Brief's `hook_style`, scores >8.5 on viral metrics

**Content Strategist:**
- Role: Scriptwriter & Logic Check
- Responsibilities: Writes full script following Brief's `narrative_arc`

**Visual Designer:**
- Role: Art Director
- Responsibilities: Selects images matching `image_arc` from local library + Pexels
- Tools: `sync_image_library`, `search_pexels_with_fallback`, `verify_visual_consistency`

**QA Specialist:**
- Role: Quality Control
- Responsibilities: Checks against Brief + User Requirements, triggers human approval

**Publisher:**
- Role: Delivery
- Responsibilities: Renders slides, uploads to Drive (slides + metadata.json in ONE call), returns verification info
- **Key Change**: Does NOT send email (Orchestrator handles this after verification)

### 3.2 Tools

| Tool | Owner | Purpose |
|------|-------|---------|
| `read_format_library` | Creative Director | Read proven viral formats |
| `TavilySearch` | Creative Director, Hook Agent | Web research |
| `get_brief_fields` | All Specialists | Retrieve brief fields via brief_id |
| `sync_image_library` | Visual Designer | Refresh local image metadata |
| `search_pexels_with_fallback` | Visual Designer | Pexels search with auto-fallback |
| `verify_visual_consistency` | Visual Designer | Check image consistency |
| `select_best_fitting_image` | Visual Designer | Pick best image from candidates |
| `request_human_approval` | QA Specialist | Pause for human review |
| `save_locally` | QA Specialist | Save approved metadata.json |
| `setup_project_folder` | Publisher | Create project structure + Drive folder |
| `read_metadata_file` | Publisher | Read approved metadata.json |
| `render_slide` | Publisher | Render HTML slide to PNG |
| `upload_to_drive` | Publisher | Upload all files (slides + metadata.json) |
| `verify_drive_upload` | Orchestrator | Double-verify Drive upload |
| `send_email_notification` | Orchestrator | Send completion email |

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

1.  **Trigger**: User runs agent with topic and requirements
2.  **Strategy**: Orchestrator delegates to Creative Director
3.  **Creative Brief**: Director creates brief, stores in state with `brief_id`
4.  **Hook**: Hook Agent generates hooks (uses `get_brief_fields`)
5.  **Content**: Strategist writes script (uses `get_brief_fields`)
6.  **Visual**: Designer selects images from library + Pexels
7.  **QA**: Specialist reviews, saves metadata.json, triggers human approval
8.  **Render**: Publisher renders slides
9.  **Upload**: Publisher uploads slides + metadata.json in ONE call
10. **Verify (Step 1)**: Publisher verifies upload
11. **Verify (Step 2)**: Orchestrator independently verifies Drive upload
12. **Email**: Orchestrator sends completion email (ONLY if verification passes)
13. **Report**: Orchestrator reports success to user with Drive link

**Retry Loop**: If verification fails at step 11, Orchestrator sends back to Publisher for retry

## 6. Technical Stack

-   **Framework**: LangGraph with DeepAgents
-   **LLM**: Gemini 1.5/2.5 Pro (rotating API keys)
-   **Browser**: Playwright (Chromium)
-   **Storage**: Local FS + Google Drive API
-   **Skills**: Context-efficient brief management via `brief_id`
-   **Pexels**: Auto-fallback search with Single Protagonist Rule

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
TOKEN_REFRESH_POLL_TIMEOUT=60  # Max seconds to wait for workflow (increased to 60s)

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
2. The agent will automatically (NON-BLOCKING):
   - Fetch the token from your private GitHub repo on startup
   - Check if the token expires within 40 minutes
   - Trigger a GitHub Actions workflow to refresh if needed (in background)
   - **Continue immediately** without waiting (no startup delay!)
   - Verify refresh completion only when Drive is needed (~10 minutes later)

#### Usage in Code
```python
from tiktok_slideshow_agent.tools.agent_tools import initialize_google_drive

# Call this BEFORE starting the agent (optional but recommended)
await initialize_google_drive()

# Agent starts immediately - no waiting!
# Token refresh happens in background during agent work
```

**Note**: If you don't call this, the agent will auto-initialize on first Drive operation.
However, calling it at startup allows the token refresh to happen in parallel with agent work,
ensuring the token is ready when the publisher needs it (~10 minutes later).

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

The agent automatically validates and refreshes tokens (non-blocking). To test this locally:

```python
# test_token_validation.py
import asyncio
import time
from tiktok_slideshow_agent.tools.agent_tools import initialize_google_drive

async def test_validation():
    print("Testing token validation (non-blocking)...\n")

    start = time.time()
    token_data = await initialize_google_drive()
    elapsed = time.time() - start

    print(f"\n✅ Returned in {elapsed:.2f}s (instant if refresh triggered!)")
    print(f"Token expires at: {token_data.get('expiry')}")
    print("\nIf refresh was triggered, it's happening in background.")
    print("Verification will occur when Drive is actually needed.")

if __name__ == "__main__":
    asyncio.run(test_validation())
```

Run it:
```bash
python test_token_validation.py
```

### Important Notes

- **Non-Blocking Refresh**: Token refresh happens in background - agent starts instantly!
- **Intelligent Timing**: Refresh is triggered at startup but verified only when Drive is needed
- **No Browser Auth**: No browser authentication needed - everything is automated
- **40-Min Threshold**: Token is refreshed automatically if expiring within 40 minutes
- **60s Timeout**: Workflow has 60 seconds to complete (usually takes 20-40s)
- **Smart Fallback**: If refresh times out but token still valid for >5 mins, agent proceeds
- **GitHub Actions**: Your `refresh_google_token.yml` workflow must be properly configured
- **Security**: Keep your `GITHUB_TOKEN` secure and never commit it to git
