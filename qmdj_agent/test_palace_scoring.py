import json
from qmdj_agent.tools.qimen import qmdj_chart_api, calculate_box_energy, calculate_score

def test_palace_scoring():
    # Test with a specific timestamp
    timestamp = "2025-12-26T21:00:00"
    print(f"Testing palace-specific scoring for timestamp: {timestamp}")
    
    chart_json = qmdj_chart_api.invoke({"timestamp": timestamp})
    energy_json = calculate_box_energy.invoke({"chart_json": chart_json})
    
    # Test Palaces:
    # Palace 4: 休门(W), 天任(E), 值符(E). Palace Element: Wood. Energy: 150%.
    # Palace 7: 杜门(W), 天蓬(W), 玄武(W). Palace Element: Metal. Energy: 20%.
    
    palaces_to_test = [4, 7, 1]
    
    for p_num in palaces_to_test:
        print(f"\n--- Palace {p_num} Scoring ---")
        score_output = calculate_score.invoke({
            "palace_num": p_num,
            "chart_json": chart_json,
            "energy_json": energy_json
        })
        print(score_output)

if __name__ == "__main__":
    test_palace_scoring()
