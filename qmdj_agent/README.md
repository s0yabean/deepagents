# 🔮 QMDJ Divination Agent

A conversational Qi Men Dun Jia (奇门遁甲) divination agent built with the deepagents framework.

## Overview

This agent provides interactive QMDJ divination readings through a multi-specialist architecture:

- **Orchestrator**: Manages conversation flow and decides when to ask questions vs provide readings
- **Chart Reader**: Fetches and parses QMDJ charts for the current time window
- **Symbol Interpreter**: Analyzes chart symbols in context of user questions
- **Strategy Advisor**: Generates actionable recommendations based on favorable palaces

## Features

- ✨ **Conversational Interface**: Asks clarifying questions instead of just delivering reports
- 🎯 **Context-Aware Analysis**: Interprets symbols based on question type (business, relationship, health, etc.)
- ⚖️ **Probabilistic Judgments**: Provides weighted yes/no answers with confidence scores
- 🧭 **Actionable Strategies**: Specific recommendations for timing, direction, and approach
- 🤔 **Ambiguity Resolution**: Identifies when symbols have multiple meanings and asks for context

## 🚀 Quickstart

**Prerequisites**: Install [uv](https://docs.astral.sh/uv/) package manager:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Ensure you are in the `qmdj_agent` directory:
```bash
cd qmdj_agent
```

Install packages:
```bash
uv sync
```

Set your API keys in `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Usage

### LangGraph Studio

Run a local LangGraph server with Studio interface:

```bash
langgraph dev
```

This will open LangGraph Studio in your browser where you can:
- Ask divination questions
- See the agent's reasoning process
- View specialist agent interactions
- Track conversation history

### Example Questions

Try asking questions like:

- "Should I invest in this new business opportunity?"
- "Is this a good time to start a new relationship?"
- "Should I accept this job offer?"
- "What's the outlook for my current project?"

The agent will:
1. Fetch the current QMDJ chart
2. Analyze symbols relevant to your question
3. Ask clarifying questions if needed
4. Provide a reading with probability, reasoning, and recommendations

## Architecture

### Multi-Specialist System

```
Orchestrator (Dialogue Manager)
    ├── Chart Reader (Data Fetching)
    ├── Symbol Interpreter (Analysis)
    └── Strategy Advisor (Recommendations)
```

### Conversation Flow

1. **User asks question** → Orchestrator receives it
2. **Parallel delegation** → All 3 specialists work simultaneously
3. **Review findings** → Orchestrator examines specialist reports
4. **Decision point**:
   - Sufficient context? → Provide complete reading
   - Ambiguity exists? → Ask 2-3 clarifying questions
5. **Final reading** → Probability + reasoning + recommendations

## Customization

### Change the Model

Edit `agent.py` to use different models:

```python
# Using Claude
from langchain.chat_models import init_chat_model
model = init_chat_model(model="anthropic:claude-sonnet-4-5-20250929", temperature=0.3)

# Using GPT-4
model = init_chat_model(model="openai:gpt-4o", temperature=0.3)

# Using Gemini (default)
from langchain_google_genai import ChatGoogleGenerativeAI
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-thinking-exp", temperature=0.3)
```

### Modify Prompts

Edit `qmdj_agent/prompts.py` to customize:
- Orchestrator conversation style
- Symbol interpretation guidelines
- Strategy recommendation formats

### Add Real QMDJ API

Currently uses placeholder data. To integrate a real QMDJ API:

1. Edit `qmdj_agent/tools.py`
2. Update `qmdj_chart_api()` function
3. Add your API credentials to `.env`

Example:
```python
@tool
def qmdj_chart_api(timestamp: str = None) -> str:
    import requests
    response = requests.get(
        "https://your-qmdj-api.com/chart",
        params={"timestamp": timestamp},
        headers={"Authorization": f"Bearer {os.getenv('QMDJ_API_KEY')}"}
    )
    return response.json()
```

### Extend Symbol Database

Edit the `symbol_lookup()` function in `qmdj_agent/tools.py` to add more symbols or interpretations.

## File Structure

```
qmdj_agent/
├── agent.py                    # Main orchestrator
├── qmdj_agent/
│   ├── __init__.py
│   ├── prompts.py             # System prompts for all agents
│   └── tools.py               # QMDJ-specific tools
├── pyproject.toml             # Dependencies
├── langgraph.json             # LangGraph configuration
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## How It Works

### 1. Chart Reading
The Chart Reader specialist fetches QMDJ data for the current 2-hour Chinese time period (时辰) and parses all 9 palaces with their symbols.

### 2. Symbol Interpretation
The Symbol Interpreter analyzes:
- **Doors (八门)**: Action/status indicators (生门, 死门, etc.)
- **Stars (九星)**: Quality of situation (天辅, 天蓬, etc.)
- **Stems (天干)**: Specific influences (丙, 丁, etc.)
- **Elements (五行)**: Elemental interactions (生, 克 relationships)

### 3. Strategic Recommendations
The Strategy Advisor generates:
- **Directional guidance**: Which compass direction to favor
- **Timing recommendations**: Best time periods to act
- **Elemental strategies**: Colors, materials, people to involve
- **Risk mitigation**: What to avoid and backup plans

### 4. Interactive Dialogue
The Orchestrator decides whether to:
- Provide a complete reading (if context is clear)
- Ask clarifying questions (if ambiguity exists)
- Request more information (if constraints are unclear)

## Example Consultation

**User**: "Should I invest in this new business opportunity?"

**Agent**: "I see mixed signals in your chart. Before giving a reading:
1. What's your timeline - do you need to decide this week or can you wait?
2. The chart shows 丙 (transformation energy) - are you comfortable with potential chaos/restructuring?
3. Do you have partners involved, or is this solo?"

**User**: "I need to decide by Friday. I'm okay with some risk. It's a partnership."

**Agent**: "**Reading: 68% Favorable (Moderate-Strong)**

**Key Factors:**
- 生门 (Growth Door) in your wealth palace indicates profit potential
- Partnership energy is supported by 天辅 (Helpful Star)
- 丙 suggests transformation - expect changes to original plan
- Minor concern: 死门 in timing palace suggests delays

**Recommended Actions:**
1. Sign agreements in NW direction if possible
2. Optimal timing: Thursday 11am-1pm (午时)
3. Involve a partner with 木 (Wood) element for best results

**Caution:**
- Avoid finalizing on Friday (死门 influence)
- Be prepared for 1-2 unexpected changes"

## ☁️ Deployment

To deploy this agent to production using **LangGraph Cloud**:

1.  Go to the [LangChain UI](https://smith.langchain.com/).
2.  Navigate to your deployment (or create a new one linked to this repo).
3.  Click the **+ New Revision** button.
4.  Select the branch you want to deploy (e.g., `develop`).
5.  Click **Submit**.

The system will automatically pull the latest code from your remote repository and deploy the new revision.

## 📚 Resources

- **[Deepagents Documentation](https://docs.langchain.com/oss/python/deepagents/overview)** - Framework overview
- **[LangGraph Platform](https://langchain-ai.github.io/langgraph/)** - Platform documentation
- **[Qi Men Dun Jia Basics](https://en.wikipedia.org/wiki/Qimen_Dunjia)** - QMDJ background

## License

MIT
