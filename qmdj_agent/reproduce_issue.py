from qmdj_agent.tools.chart_generator.qimen_generator import QimenGenerator
from datetime import datetime
import json

# Target time: 2026-01-12 11:00
dt = datetime(2026, 1, 12, 11, 0, 0)
gen = QimenGenerator(dt.year, dt.month, dt.day, dt.hour)
chart_data = gen.generate()

print(json.dumps(chart_data, ensure_ascii=False, indent=2))

# Helper to find symbols
def find_symbol(data, symbol):
    for p_num, p_data in data['palaces'].items():
        if isinstance(p_data, dict):
             if (p_data.get('deity') == symbol or 
                 p_data.get('door') == symbol or 
                 p_data.get('star') == symbol):
                 return p_num
    return "Not Found"

print("\n--- Key Symbol Locations ---")
print(f"Partners (Liu He / 六合): Palace {find_symbol(chart_data, '六合')}")
print(f"Business (Sheng Men / 生门): Palace {find_symbol(chart_data, '生门')}")
print(f"Capital (Wu / 戊): Palace {find_symbol(chart_data, '戊')}") # Wu is a stem, logic slightly different usually, but printed in chart
print(f"Emptiness (Empty Palaces): {chart_data.get('empty_death', 'None')}")

print("\n--- Testing Retrieval & Verification Tool ---")
from qmdj_agent.tools.qimen import verify_palace_attributes

# Test Palace 4 (Should be EMPTY)
print("\n[TEST] Verifying Palace 4 (Expected: EMPTY):")
print(verify_palace_attributes.invoke({"palace_num": 4, "chart_json": json.dumps(chart_data)}))

# Test Palace 1 (Should be SOLID)
print("\n[TEST] Verifying Palace 1 (Expected: SOLID/NOT EMPTY):")
print(verify_palace_attributes.invoke({"palace_num": 1, "chart_json": json.dumps(chart_data)}))
