from qmdj_agent.tools.sanitizer import sanitize_output, sanitize_agent_names

def test_sanitizers():
    print("--- Testing Output Sanitizer ---")
    # Test case 1: No jargon
    print("Testing with no jargon...")
    result_clean = sanitize_output.invoke({"text": "The outlook for your career is very favorable. You should take action soon."})
    print(f"Result: {result_clean}")
    assert result_clean == "success, no jargon detected."

    # Test case 2: Jargon substring
    print("\nTesting with 'QMDJ' substring...")
    result_jargon = sanitize_output.invoke({"text": "This confirms the qmdj_reading is accurate."})
    print(f"Result: {result_jargon}")
    assert "QMDJ" in result_jargon
    
    print("\n--- Testing Agent Name Sanitizer ---")
    # Test case 3: No agent names
    print("Testing with no agent names...")
    result_no_names = sanitize_agent_names.invoke({"text": "Our analysis shows strong energy in the north."})
    print(f"Result: {result_no_names}")
    assert result_no_names == "success"
    
    # Test case 4: Single agent name
    print("\nTesting with 'chart-reader'...")
    result_name1 = sanitize_agent_names.invoke({"text": "According to the chart-reader, the structure is solid."})
    print(f"Result: {result_name1}")
    assert "chart-reader" in result_name1
    
    # Test case 5: Case insensitive agent name
    print("\nTesting with 'ENERGY-ANALYZER'...")
    result_name2 = sanitize_agent_names.invoke({"text": "The ENERGY-ANALYZER reports low values."})
    print(f"Result: {result_name2}")
    assert "energy-analyzer" in result_name2

    print("\nAll tests passed!")

if __name__ == "__main__":
    test_sanitizers()
