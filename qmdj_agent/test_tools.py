"""Quick test to verify QMDJ agent structure."""

from qmdj_agent.tools import qmdj_chart_api, symbol_lookup, five_element_interaction, reflect_on_reading

# Test 1: Chart API
print("=" * 60)
print("TEST 1: QMDJ Chart API")
print("=" * 60)
chart_result = qmdj_chart_api.invoke({"timestamp": "2025-12-21T21:00:00"})
print(chart_result[:500] + "...\n")

# Test 2: Symbol Lookup
print("=" * 60)
print("TEST 2: Symbol Lookup")
print("=" * 60)
symbol_result = symbol_lookup.invoke({"symbol_name": "生門", "context": "business"})
print(symbol_result + "\n")

# Test 3: Element Interaction
print("=" * 60)
print("TEST 3: Element Interaction")
print("=" * 60)
element_result = five_element_interaction.invoke({"element1": "Wood", "element2": "Fire"})
print(element_result + "\n")

# Test 4: Reflection
print("=" * 60)
print("TEST 4: Reflection Tool")
print("=" * 60)
reflect_result = reflect_on_reading.invoke({"reflection": "Testing the reflection mechanism"})
print(reflect_result + "\n")

print("✅ All tools working correctly!")
