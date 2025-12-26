import json
from qmdj_agent.tools.chart_generator.qimen_generator import QimenGenerator
from qmdj_agent.tools.general import get_current_time
from qmdj_agent.tools.qimen import qmdj_chart_api, calculate_box_energy
from datetime import datetime

print("=" * 70)
print("QMDJ CHART GENERATOR - CURRENT TIME")
print("=" * 70)
print()

# Method 1: Using tools (what the agent uses)
print("📊 Generating chart using tools...")
timestamp = get_current_time.invoke({})
print(f"Current timestamp: {timestamp}")
print()

chart_json = qmdj_chart_api.invoke({"timestamp": timestamp})
print("JSON Output (first 300 chars):")
print(chart_json)
print()

# Calculate Energy
print("⚡ Calculating energy levels...")
energy_json = calculate_box_energy.invoke({"chart_json": chart_json})
energy_data = json.loads(energy_json)
print()

now = datetime.now()
gen = QimenGenerator(now.year, now.month, now.day, now.hour)
print(gen.to_string(energy_data=energy_data))

