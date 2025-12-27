import json
from qmdj_agent.tools.qimen import qmdj_chart_api, calculate_score

def test_fix():
    timestamp = "2025-12-26T21:00:00"
    chart_json = qmdj_chart_api.invoke({"timestamp": timestamp})
    
    # Simulate the bad input that caused the crash
    # Case 1: energy_json is a string that parses to an int
    print("\n--- Testing Case 1: energy_json is '150' ---")
    try:
        output = calculate_score.invoke({
            "palace_num": 1,
            "chart_json": chart_json,
            "energy_json": "150"
        })
        print("Success! Output received:")
        print(output)
    except Exception as e:
        print(f"Failed! Error: {e}")

    # Case 2: energy_json is a dict but palace key is an int
    print("\n--- Testing Case 2: energy_json has int value for palace ---")
    bad_energy_dict = {"1": 150}
    try:
        output = calculate_score.invoke({
            "palace_num": 1,
            "chart_json": chart_json,
            "energy_json": json.dumps(bad_energy_dict)
        })
        print("Success! Output received:")
        print(output)
    except Exception as e:
        print(f"Failed! Error: {e}")

if __name__ == "__main__":
    test_fix()
