from qmdj_agent.tools.qimen import five_element_interaction, get_symbol_element, PALACE_ELEMENTS

def test_elements():
    print("--- Testing Five Element Interactions ---")
    # Generating
    print(five_element_interaction.invoke({"element1": "Wood", "element2": "Fire"}))
    # Draining
    print(five_element_interaction.invoke({"element1": "Fire", "element2": "Wood"}))
    # Controlling
    print(five_element_interaction.invoke({"element1": "Wood", "element2": "Earth"}))
    # Weakening
    print(five_element_interaction.invoke({"element1": "Earth", "element2": "Wood"}))
    # Harmony
    print(five_element_interaction.invoke({"element1": "Water", "element2": "Water"}))
    
    print("\n--- Testing Symbol Metadata ---")
    symbols = ["休门", "天芮", "值符", "甲", "乙", "丙"]
    for s in symbols:
        print(f"{s}: {get_symbol_element(s)}")
        
    print("\n--- Testing Palace Elements ---")
    for p in range(1, 10):
        print(f"Palace {p}: {PALACE_ELEMENTS[p]}")

if __name__ == "__main__":
    test_elements()
