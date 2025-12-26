# 🔮 QMDJ Divination Agent

A conversational Qi Men Dun Jia (奇门遁甲) divination agent built with the `deepagents` framework. This agent provides interactive QMDJ readings through a multi-specialist architecture, combining ancient wisdom with modern agentic intelligence.

---

## 🚀 Quick Start

### 1. Prerequisites
Install [uv](https://docs.astral.sh/uv/) package manager:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Setup
Navigate to the directory and install dependencies:
```bash
cd qmdj_agent
uv sync
```

### 3. Configuration
Set your API keys in the `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 4. Run with LangGraph Studio
Start the local development server:
```bash
langgraph dev
```
LangGraph Studio will open at `http://localhost:2024`.

---

## 🛡️ The QMDJ Agent Army

This system uses a **Master-Specialist** architecture to weave cosmic data into human wisdom.

### 1. The Master (Orchestrator)
The "Divination Master" who manages the specialists. He synthesizes complex, sometimes contradictory, metaphysical data into a clear, empowering narrative. He follows a strict **Planning -> Execution -> Synthesis** loop.

### 2. The Specialists
*   **👁️ Chart Reader**: Fetches the raw Qimen chart for the current time window (Simplified Chinese).
*   **⚡ Energy Analyzer**: Calculates palace strength (100/150/20) based on Death/Emptiness, Tai Sui, and Diagonal Overflow.
*   **🏮 Symbol Interpreter**: Analyzes Doors, Stars, and Deities. Provides quantitative **Palace Favorability Scores**.
*   **🔮 Pattern Predictor**: Identifies synchronicities and multi-palace connections to make bold, testable predictions.
*   **🎲 Probabilistic Agent**: Runs 1,000 Monte Carlo simulations to quantify the "Luck" factor and volatility.
*   **⚖️ Contrarian Agent**: Acts as Devil's Advocate, challenging assumptions and identifying blind spots.
*   **⚔️ Strategy Advisor**: Generates the Action Plan, including **Elemental Remedies** (bridge elements) to fix bad luck.
*   **🌍 Context Advisor**: Grounds the reading in reality by searching for industry data, news, and market trends.

---

## ✨ Key Features

- **✨ Conversational Interface**: Asks clarifying questions instead of just delivering reports.
- **🎯 Context-Aware Analysis**: Interprets symbols based on question type (Business, Relationship, Health, etc.).
- **⚖️ Probabilistic Judgments**: Provides weighted favorability scores and Monte Carlo risk assessments.
- **🧭 Actionable Strategies**: Specific recommendations for timing, direction, and elemental remedies.
- **🤔 Ambiguity Resolution**: Identifies conflicting signals (e.g., Good Door + Bad Star) and asks for context.
- **📈 Intelligence Loop**: A rigorous data chain: **Chart -> Energy -> Score -> Strategy**.

---

## 📝 Example Consultation

**User**: "Should I invest in this new business opportunity?"

**Agent**: "I see mixed signals in your chart. Before giving a reading:
1. What's your timeline - do you need to decide this week?
2. The chart shows 丙 (transformation energy) - are you comfortable with potential disruption?
3. Is this a partnership or solo venture?"

**User**: "I need to decide by Friday. I'm okay with risk. It's a partnership."

**Agent**: "**Reading: 68% Favorable (Moderate-Strong)**
- **Success Probability**: 72% (Monte Carlo)
- **Key Factors**: 生门 (Growth) in wealth palace indicates profit potential.
- **Remedy**: Use a **Water** bridge to resolve the Metal/Wood conflict in your career palace."

---

## 🛠️ Technical Details

### File Structure
```
qmdj_agent/
├── agent.py                    # Main orchestrator & specialist definitions
├── qmdj_agent/
│   ├── prompts/                # Modular system prompts
│   ├── tools/                  # QMDJ-specific tools (qimen.py, simulation.py)
│   └── knowledge_base/         # Simplified Chinese symbol data
├── pyproject.toml             # Dependencies
└── langgraph.json             # LangGraph configuration
```

### Customization
- **Change Model**: Edit `agent.py` to switch between Gemini, Claude, or GPT-4.
- **Modify Prompts**: Edit files in `qmdj_agent/prompts/` to adjust agent personalities.
- **Extend Tools**: Add new metaphysical logic to `qmdj_agent/tools/qimen.py`.

---

## 🧪 Verification
Run the following scripts to verify the system:
- `python plot_current_chart.py`: Generate a visual chart with energy data.
- `python test_palace_scoring.py`: Test the weighted scoring logic.
- `python verify_agent_config.py`: Verify tool registration for all specialists.

---

## 📚 Resources
- [Deepagents Documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [LangGraph Platform](https://langchain-ai.github.io/langgraph/)
- [Qi Men Dun Jia Basics](https://en.wikipedia.org/wiki/Qimen_Dunjia)

## License
MIT
