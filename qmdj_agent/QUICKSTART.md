# 🚀 Quick Start Guide - QMDJ Divination Agent

## Ready to Run! ✅

Your QMDJ divination agent is fully set up and ready to use.

## Start the Agent (2 steps)

### 1. Navigate to the directory
```bash
cd /Users/mindreader/Desktop/deepagents-quickstarts/qmdj_agent
```

### 2. Start LangGraph Studio
```bash
langgraph dev
```

That's it! LangGraph Studio will open in your browser at `http://localhost:2024`

## What You'll See

The Studio interface will show:
- **Graph visualization**: See the orchestrator and 3 specialist agents
- **Chat interface**: Ask divination questions
- **Agent reasoning**: Watch specialists work in parallel
- **Tool calls**: See chart fetching, symbol lookup, etc.

## Example Questions to Try

### Business/Investment
```
"Should I invest in this new business opportunity?"
"Is this a good time to launch my product?"
"Should I accept this partnership offer?"
```

### Relationships
```
"Is this a good time to start a new relationship?"
"Should I have that difficult conversation today?"
"Will this partnership work out?"
```

### Career
```
"Should I accept this job offer?"
"Is this the right time to ask for a promotion?"
"Should I start my own business now?"
```

### General
```
"What's the outlook for my current project?"
"Should I make this major decision today?"
"Is this timing favorable for my plans?"
```

## What the Agent Will Do

1. **Fetch Chart**: Get QMDJ chart for current time (e.g., 酉时 17:00-19:00)
2. **Analyze Symbols**: Examine all 9 palaces for relevant indicators
3. **Ask Questions** (if needed): Clarify ambiguities or constraints
4. **Provide Reading**: Give probability, reasoning, and recommendations

## Example Interaction

**You**: "Should I invest in this opportunity?"

**Agent**: "I see mixed signals in your chart. Before giving a reading:
1. What's your timeline - do you need to decide this week?
2. The chart shows 丙 (transformation) - are you comfortable with disruption?
3. Is this a partnership or solo venture?"

**You**: "I need to decide by Friday. I'm okay with risk. It's a partnership."

**Agent**: "**Reading: 68% Favorable (Moderate-Strong)**

**Key Factors:**
- 生门 (Growth Door) in wealth palace = profit potential
- 天辅 (Helpful Star) supports partnerships
- 丙 indicates transformation - expect plan changes
- 死门 in timing palace suggests minor delays

**Recommended Actions:**
1. Sign agreements in NW direction if possible
2. Best timing: Thursday 11am-1pm (午时)
3. Involve partner with 木 (Wood) element

**Cautions:**
- Avoid finalizing on Friday (死门 influence)
- Prepare for 1-2 unexpected changes"

## Architecture Overview

```
You ask question
    ↓
Orchestrator (Dialogue Manager)
    ↓
Delegates to 3 specialists (parallel):
    ├── Chart Reader → Fetches QMDJ data
    ├── Symbol Interpreter → Analyzes meanings
    └── Strategy Advisor → Creates recommendations
    ↓
Orchestrator synthesizes findings
    ↓
Asks questions OR provides reading
```

## Files Overview

- **agent.py**: Main orchestrator setup
- **qmdj_agent/prompts.py**: System prompts for all agents
- **qmdj_agent/tools.py**: QMDJ tools (chart API, symbol lookup, etc.)
- **README.md**: Full documentation
- **IMPLEMENTATION_SUMMARY.md**: Technical details

## Troubleshooting

### Port Already in Use
If you see "port 2024 already in use":
```bash
# Stop the other langgraph dev process first
# Or use a different port:
langgraph dev --port 2025
```

### Missing API Key
If you see API key errors:
1. Check `.env` file has `GOOGLE_API_KEY` set
2. Or set it in your shell:
```bash
export GOOGLE_API_KEY=your_key_here
langgraph dev
```

## Next Steps

### Customize the Agent
- Edit `qmdj_agent/prompts.py` to change conversation style
- Edit `qmdj_agent/tools.py` to add real QMDJ API
- Edit `agent.py` to change the model (Claude, GPT-4, etc.)

### Add Real Data
Replace placeholder in `qmdj_chart_api()` with actual API call:
```python
@tool
def qmdj_chart_api(timestamp: str = None) -> str:
    import requests
    response = requests.get("https://your-qmdj-api.com/chart", ...)
    return response.json()
```

## Support

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Deepagents Docs**: https://docs.langchain.com/oss/python/deepagents/overview
- **Test Tools**: Run `uv run python test_tools.py` to verify setup

---

**Ready?** Just run: `langgraph dev` 🚀
