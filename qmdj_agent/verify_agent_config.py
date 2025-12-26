from agent import symbol_interpreter, probabilistic_agent, qmdj_strategy_advisor

def verify_config():
    print("--- Verifying Specialist Tool Registration ---")
    
    def get_tool_names(specialist):
        names = []
        for t in specialist["tools"]:
            if hasattr(t, "name"):
                names.append(t.name)
            else:
                names.append(t.__name__)
        return names

    # Symbol Interpreter
    si_tools = get_tool_names(symbol_interpreter)
    print(f"\nSymbol Interpreter Tools: {si_tools}")
    expected_si = ["calculate_score", "calculate_box_energy", "compare_palaces"]
    for t in expected_si:
        assert t in si_tools, f"Missing {t} in Symbol Interpreter"
    
    # Probabilistic Agent
    pa_tools = get_tool_names(probabilistic_agent)
    print(f"Probabilistic Agent Tools: {pa_tools}")
    assert "calculate_score" in pa_tools, "Missing calculate_score in Probabilistic Agent"
    
    # Strategy Advisor
    sa_tools = get_tool_names(qmdj_strategy_advisor)
    print(f"Strategy Advisor Tools: {sa_tools}")
    expected_sa = ["five_element_interaction", "calculate_box_energy", "get_elemental_remedy"]
    for t in expected_sa:
        assert t in sa_tools, f"Missing {t} in Strategy Advisor"
    
    print("\n✅ All specialist tools correctly registered!")

if __name__ == "__main__":
    verify_config()
