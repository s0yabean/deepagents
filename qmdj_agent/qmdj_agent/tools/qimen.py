"""QMDJ-specific tools for the QMDJ agent."""

from langchain_core.tools import tool
from typing import Dict, List, Optional
import json
from datetime import datetime
from qmdj_agent.tools.chart_generator.qimen_generator import QimenGenerator

# ==============================================================================
# QMDJ Chart Generation Tool
# ==============================================================================

@tool(parse_docstring=True)
def qmdj_chart_api(timestamp: str) -> str:
    """Generates a Qimen Dunjia chart for a specific date and time.
    
    Args:
        timestamp: ISO 8601 formatted timestamp (e.g., '2023-10-27T10:00:00')
    """
    try:
        dt = datetime.fromisoformat(timestamp)
    except ValueError:
        return json.dumps({"error": "Invalid timestamp format. Use ISO 8601 (e.g., 2023-10-27T10:00:00)"})
        
    # Generate Chart (calculations use GMT+8 via lunar-python)
    try:
        generator = QimenGenerator(dt.year, dt.month, dt.day, dt.hour)
        chart_data = generator.generate()
        return json.dumps(chart_data, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Chart generation failed: {str(e)}"})

# ==============================================================================
# Energy Analysis Tools
# ==============================================================================

def find_palace_with_stem(chart_data: dict, stem: str) -> int:
    """Find which palace contains the given heaven stem by searching the chart."""
    palaces = chart_data.get("palaces", {})
    for palace_num in range(1, 10):
        palace_data = palaces.get(str(palace_num), {})
        heaven_stem = palace_data.get("heaven_stem", "")
        if stem in heaven_stem:
            return palace_num
    return 0

def get_palace_for_branch(branch: str) -> int:
    """Map earthly branch (zodiac) to palace number."""
    branch_to_palace = {
        "子": 1, "未": 2, "申": 2, "卯": 3, "辰": 4, "巳": 4,
        "戌": 6, "亥": 6, "酉": 7, "丑": 8, "寅": 8, "午": 9,
    }
    return branch_to_palace.get(branch, 0)

def get_diagonal_palace(palace: int) -> int:
    """Get diagonal opposite palace. Palace 5 (center) has no diagonal."""
    diagonal_map = {1: 9, 2: 8, 3: 7, 4: 6, 6: 4, 7: 3, 8: 2, 9: 1, 5: 0}
    return diagonal_map.get(palace, 0)

@tool(parse_docstring=True)
def calculate_box_energy(chart_json: str) -> str:
    """Calculate energy levels for all 9 palaces based on Death/Emptiness, Tai Sui, and overflow.
    
    Args:
        chart_json: JSON string from qmdj_chart_api containing chart data
    """
    try:
        chart = json.loads(chart_json)
        
        # Step 1: Extract year stem and branch
        year_ganzhi = chart.get("gan_zhi", {}).get("year", "")
        if len(year_ganzhi) != 2:
            return json.dumps({"error": "Invalid year gan_zhi format"})
        
        year_stem = year_ganzhi[0]
        year_branch = year_ganzhi[1]
        
        # Step 2: Find palaces for year stem and branch
        tai_sui_palaces = set()
        year_stem_palace = find_palace_with_stem(chart, year_stem)
        year_branch_palace = get_palace_for_branch(year_branch)
        
        if year_stem_palace: tai_sui_palaces.add(year_stem_palace)
        if year_branch_palace: tai_sui_palaces.add(year_branch_palace)
        
        # Step 3: Identify Death/Emptiness palaces
        empty_death_str = chart.get("empty_death", "")
        de_palaces = set()
        for char in empty_death_str:
            palace = get_palace_for_branch(char)
            if palace: de_palaces.add(palace)
        
        # Step 4: Initialize all palaces at 100%
        energy_data = {}
        for i in range(1, 10):
            energy_data[str(i)] = {"energy": 100, "modifier": [], "details": []}
        
        # Step 5: Apply Death/Emptiness (reduce to 20%)
        for palace in de_palaces:
            energy_data[str(palace)]["energy"] = 20
            energy_data[str(palace)]["modifier"].append("death_emptiness")
            energy_data[str(palace)]["details"].append("Death/Emptiness: 100% → 20%")
        
        # Step 6: Apply Tai Sui boost (increase to 150%)
        for palace in tai_sui_palaces:
            current = energy_data[str(palace)]["energy"]
            if current == 20:
                energy_data[str(palace)]["energy"] = 150
                energy_data[str(palace)]["modifier"].append("tai_sui_override")
                energy_data[str(palace)]["details"].append(f"Tai Sui boost: 20% → 150%")
            else:
                energy_data[str(palace)]["energy"] = 150
                energy_data[str(palace)]["modifier"].append("tai_sui")
                energy_data[str(palace)]["details"].append(f"Tai Sui boost: 100% → 150%")
        
        # Step 7: Apply diagonal overflow
        for tai_sui_palace in tai_sui_palaces:
            diagonal = get_diagonal_palace(tai_sui_palace)
            if diagonal == 0: continue
            
            diagonal_str = str(diagonal)
            if diagonal not in tai_sui_palaces:
                if diagonal in de_palaces:
                    energy_data[diagonal_str]["energy"] = 100
                    energy_data[diagonal_str]["modifier"].append("overflow_from_tai_sui")
                    energy_data[diagonal_str]["details"].append(f"Diagonal overflow from Palace {tai_sui_palace}: 20% → 100%")
                else:
                    energy_data[diagonal_str]["energy"] = 150
                    energy_data[diagonal_str]["modifier"].append("overflow_from_tai_sui")
                    energy_data[diagonal_str]["details"].append(f"Diagonal overflow from Palace {tai_sui_palace}: 100% → 150%")
        
        # Step 8: Format modifiers
        for palace_key in energy_data:
            if not energy_data[palace_key]["modifier"]:
                energy_data[palace_key]["modifier"] = "normal"
            else:
                energy_data[palace_key]["modifier"] = ", ".join(energy_data[palace_key]["modifier"])
        
        energy_data["summary"] = {
            "year_ganzhi": year_ganzhi,
            "tai_sui_palaces": sorted(list(tai_sui_palaces)),
            "death_emptiness": empty_death_str,
            "de_palaces": sorted(list(de_palaces)),
            "high_energy_palaces": sorted([int(k) for k, v in energy_data.items() if k.isdigit() and v["energy"] >= 150]),
            "low_energy_palaces": sorted([int(k) for k, v in energy_data.items() if k.isdigit() and v["energy"] == 20])
        }
        
        return json.dumps(energy_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Energy calculation failed: {str(e)}"}, ensure_ascii=False)

@tool(parse_docstring=True)
def apply_tai_sui_modifier(energy_json: str, year: int) -> str:
    """Apply Tai Sui year-based energy modifiers (DEPRECATED).
    
    Args:
        energy_json: JSON string with energy data.
        year: The year to apply modifiers for.
    """
    try:
        energy_data = json.loads(energy_json)
        energy_data["tai_sui_applied"] = f"Year {year} (STUB: Not yet implemented)"
        return json.dumps(energy_data, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Tai Sui calculation failed: {str(e)}"})

@tool(parse_docstring=True)
def detect_diagonal_overflow(chart_json: str) -> str:
    """Detect diagonal overflow patterns.
    
    Args:
        chart_json: JSON string containing chart data.
    """
    return json.dumps({
        "overflow_detected": False,
        "affected_palaces": [],
        "note": "STUB: Diagonal overflow detection not yet implemented"
    }, ensure_ascii=False, indent=2)

# ==============================================================================
# Symbol Knowledge Base Tools
# ==============================================================================

# Normalization Map: Handles Traditional Chinese variants and Abbreviations
# Maps input -> Canonical Key (Simplified Chinese)
NORMALIZE_MAP = {
    # Stars (Traditional -> Simplified)
    "天沖": "天冲",
    "天輔": "天辅",
    "天禽": "天禽", # Self-map for safety
    
    # Deities (Abbreviations/Traditional -> Full Simplified)
    "符": "值符",
    "蛇": "螣蛇",
    "陰": "太阴", # Traditional 'Yin'
    "阴": "太阴", # Simplified 'Yin' abbr
    "太陰": "太阴", # Traditional Full
    "合": "六合",
    "虎": "白虎",
    "玄": "玄武",
    "地": "九地",
    "天": "九天", # 'Heaven' abbr for Nine Heavens
}

SYMBOL_DATA = {
    # ========== 8 Doors (八門) ==========
    "休門": {"name_en": "Rest Door", "pinyin": "Xiu Men", "element": "Water", "general": "Relaxation, recovery, family, nobility.", "recommendation": "Take a step back to rest. Focus on internal matters."},
    "生門": {"name_en": "Life Door", "pinyin": "Sheng Men", "element": "Earth", "general": "Growth, profit, vitality, new beginnings.", "recommendation": "Actively pursue growth and profit. Launch new projects."},
    "傷門": {"name_en": "Injury Door", "pinyin": "Shang Men", "element": "Wood", "general": "Harm, hunting, gambling, debt collection.", "recommendation": "Be cautious of injury. Good for aggressive tasks like debt collection."},
    "杜門": {"name_en": "Delusion Door", "pinyin": "Du Men", "element": "Wood", "general": "Hiding, obstruction, secrecy, technical skills.", "recommendation": "Keep a low profile. Focus on research or technical work."},
    "景門": {"name_en": "View Door", "pinyin": "Jing Men", "element": "Fire", "general": "Beauty, documents, reputation, strategy.", "recommendation": "Focus on branding and reputation. Create a strategy."},
    "死門": {"name_en": "Death Door", "pinyin": "Si Men", "element": "Earth", "general": "Endings, stagnation, mourning, land.", "recommendation": "Accept endings. Do not start anything new. Good for land matters."},
    "驚門": {"name_en": "Fear Door", "pinyin": "Jing Men", "element": "Metal", "general": "Fear, disputes, lawsuits, panic.", "recommendation": "Prepare for disputes. Use your voice for debate."},
    "開門": {"name_en": "Open Door", "pinyin": "Kai Men", "element": "Metal", "general": "Career, opportunity, opening, public.", "recommendation": "Seize the opportunity. Open new doors in career and business."},

    # ========== 9 Stars (九星) ==========
    "天蓬": {"name_en": "Grass Star (Robber Star)", "pinyin": "Tian Peng", "element": "Water", "general": "Risk taking, intelligence, loss of wealth.", "recommendation": "Take calculated risks but secure your assets."},
    "天芮": {"name_en": "Grain Star (Problem Star)", "pinyin": "Tian Rui", "element": "Earth", "general": "Illness, problems, learning, students.", "recommendation": "Identify and fix internal problems. Focus on learning."},
    "天沖": {"name_en": "Impulse Star", "pinyin": "Tian Chong", "element": "Wood", "general": "Action, impulse, charity, sports.", "recommendation": "Take quick, decisive action. Avoid overthinking."},
    "天輔": {"name_en": "Assistant Star", "pinyin": "Tian Fu", "element": "Wood", "general": "Education, assistance, culture, nobility.", "recommendation": "Seek help from mentors. Focus on education."},
    "天禽": {"name_en": "Bird Star", "pinyin": "Tian Qin", "element": "Earth", "general": "Central, reliable, honest.", "recommendation": "Lead with honesty and reliability."},
    "天心": {"name_en": "Doctor Star", "pinyin": "Tian Xin", "element": "Metal", "general": "Leadership, authority, medical matters.", "recommendation": "Take charge and plan strategically. Focus on healing."},
    "天柱": {"name_en": "Destroyer Star", "pinyin": "Tian Zhu", "element": "Metal", "general": "Support, legal matters, rigidity.", "recommendation": "Stand firm on principles but avoid rigidity."},
    "天任": {"name_en": "Diplomat Star", "pinyin": "Tian Ren", "element": "Earth", "general": "Wealth, responsibility, real estate.", "recommendation": "Be patient and responsible. Focus on long-term wealth."},
    "天英": {"name_en": "Hero Star", "pinyin": "Tian Ying", "element": "Fire", "general": "Brightness, fame, passion, beauty.", "recommendation": "Seek fame and recognition. Be careful of burnout."},

    # ========== 8 Deities (八神) ==========
    "值符": {"name_en": "Chief", "pinyin": "Zhi Fu", "element": "Wood/Earth", "general": "The leader, protection, wealth, high status.", "recommendation": "Take the lead with confidence. You are protected."},
    "螣蛇": {"name_en": "Snake", "pinyin": "Teng She", "element": "Fire", "general": "Deception, hypocrisy, supernatural, changing.", "recommendation": "Be vigilant against deception. Adapt to changes."},
    "太阴": {"name_en": "Moon", "pinyin": "Tai Yin", "element": "Metal", "general": "Secrets, planning, darkness, female help.", "recommendation": "Plan in secret. Seek assistance from women."},
    "六合": {"name_en": "Six Harmony", "pinyin": "Liu He", "element": "Wood", "general": "Relationships, marriage, partnership, negotiation.", "recommendation": "Focus on networking and partnerships."},
    "白虎": {"name_en": "White Tiger", "pinyin": "Bai Hu", "element": "Metal", "general": "Ferocity, injury, blood, pressure.", "recommendation": "Prepare for high pressure. Avoid confrontation."},
    "玄武": {"name_en": "Black Tortoise", "pinyin": "Xuan Wu", "element": "Water", "general": "Theft, deception, loss, secrets.", "recommendation": "Guard your assets. Watch out for theft and fraud."},
    "九地": {"name_en": "Nine Earth", "pinyin": "Jiu Di", "element": "Earth", "general": "Stability, slowness, long-term, hiding.", "recommendation": "Adopt a low profile. Think long-term."},
    "九天": {"name_en": "Nine Heavens", "pinyin": "Jiu Tian", "element": "Metal", "general": "Active, fast, travel, high ambition.", "recommendation": "Aim high and move fast. Expand your horizons."},

    # ========== 10 Stems (十干) ==========
    "甲": {"name_en": "Yang Wood", "pinyin": "Jia", "general": "Noble person, leadership, the best.", "recommendation": "Act as a leader. Strive for excellence."},
    "乙": {"name_en": "Yin Wood", "pinyin": "Yi", "general": "Women, winding path, artistic, flexibility.", "recommendation": "Be flexible and adaptable. Use soft skills."},
    "丙": {"name_en": "Yang Fire", "pinyin": "Bing", "general": "Transformation, chaos, breakthrough.", "recommendation": "Create a breakthrough. Be decisive."},
    "丁": {"name_en": "Yin Fire", "pinyin": "Ding", "general": "Hope, documents, contracts, inspiration.", "recommendation": "Focus on documents and details. Look for hope."},
    "戊": {"name_en": "Yang Earth", "pinyin": "Wu", "general": "Capital, finance, assets, trust.", "recommendation": "Manage your capital. Be reliable."},
    "己": {"name_en": "Yin Earth", "pinyin": "Ji", "general": "Desire, plan, scheme, hidden resources.", "recommendation": "Plan strategically. Keep resources hidden."},
    "庚": {"name_en": "Yang Metal", "pinyin": "Geng", "general": "Enemy, competitor, lawsuit, obstacles.", "recommendation": "Prepare for competition. Overcome obstacles."},
    "辛": {"name_en": "Yin Metal", "pinyin": "Xin", "general": "Mistake, problem, crime, refinement.", "recommendation": "Correct mistakes. Refine your approach."},
    "壬": {"name_en": "Yang Water", "pinyin": "Ren", "general": "Journey, movement, change, flow.", "recommendation": "Go with the flow. Adapt to changes."},
    "癸": {"name_en": "Yin Water", "pinyin": "Gui", "general": "Network, relationship, communication.", "recommendation": "Leverage your network. Communicate discreetly."},

    # ========== 12 Branches (十二支) ==========
    "子": {"name_en": "Rat", "pinyin": "Zi", "element": "Water", "general": "Wisdom, intelligence, resourcefulness.", "recommendation": "Use your wisdom. Plan strategically."},
    "丑": {"name_en": "Ox", "pinyin": "Chou", "element": "Earth", "general": "Diligence, stability, perseverance.", "recommendation": "Work hard and persevere."},
    "寅": {"name_en": "Tiger", "pinyin": "Yin", "element": "Wood", "general": "Courage, leadership, ambition.", "recommendation": "Be courageous. Take the lead."},
    "卯": {"name_en": "Rabbit", "pinyin": "Mao", "element": "Wood", "general": "Kindness, diplomacy, creativity.", "recommendation": "Use diplomacy. Be gentle but persistent."},
    "辰": {"name_en": "Dragon", "pinyin": "Chen", "element": "Earth", "general": "Power, authority, ambition.", "recommendation": "Exercise authority. Aim high."},
    "巳": {"name_en": "Snake", "pinyin": "Si", "element": "Fire", "general": "Wisdom, intuition, change.", "recommendation": "Trust intuition. Adapt to changes."},
    "午": {"name_en": "Horse", "pinyin": "Wu", "element": "Fire", "general": "Passion, energy, visibility.", "recommendation": "Show passion. Be visible."},
    "未": {"name_en": "Goat", "pinyin": "Wei", "element": "Earth", "general": "Patience, support, detail.", "recommendation": "Be patient. Pay attention to details."},
    "申": {"name_en": "Monkey", "pinyin": "Shen", "element": "Metal", "general": "Agility, problem solving, travel.", "recommendation": "Be agile. Solve problems creatively."},
    "酉": {"name_en": "Rooster", "pinyin": "You", "element": "Metal", "general": "Precision, confidence, beauty.", "recommendation": "Be precise. Focus on quality."},
    "戌": {"name_en": "Dog", "pinyin": "Xu", "element": "Earth", "general": "Loyalty, honesty, protection.", "recommendation": "Be loyal. Protect what is important."},
    "亥": {"name_en": "Pig", "pinyin": "Hai", "element": "Water", "general": "Wealth, happiness, comfort.", "recommendation": "Enjoy the process. Focus on comfort."}
}

@tool(parse_docstring=True)
def symbol_lookup(symbol_name: str, context: str = "general") -> str:
    """Look up the meaning and recommendation of a QMDJ symbol.

    Args:
        symbol_name: The Chinese name of the symbol (e.g., '天芮', '死門', '甲').
        context: The context of the reading ('general', 'business', 'relationship', 'health'). Defaults to 'general'.
    """
    # Normalize input: strip whitespace
    key = symbol_name.strip()
    
    # Check Normalization Map (Traditional -> Simplified, Abbr -> Full)
    key = NORMALIZE_MAP.get(key, key)
    
    # Direct lookup
    data = SYMBOL_DATA.get(key)
    
    # Fallback: Try appending common suffixes if not found (e.g. user asks for "休" instead of "休門")
    if not data:
        if key + "門" in SYMBOL_DATA: data = SYMBOL_DATA[key + "門"]
        elif key + "星" in SYMBOL_DATA: data = SYMBOL_DATA[key + "星"]
        
    if not data:
        return f"Symbol '{symbol_name}' not found in database."
    
    meaning = data.get(context, data.get("general", "No description available."))
    recommendation = data.get("recommendation", "No specific recommendation available.")
    name_en = data.get("name_en", "Unknown")
    pinyin = data.get("pinyin", "")
    element = data.get("element", "Unknown")
    
    return f"""**Symbol:** {key} ({name_en} - {pinyin})
**Element:** {element}
**Context:** {context.capitalize()}
**Meaning:** {meaning}
**Recommendation:** {recommendation}"""

@tool(parse_docstring=True)
def five_element_interaction(element1: str, element2: str) -> str:
    """Analyze the interaction between two Five Elements (Wu Xing).

    Args:
        element1: The first element (Wood, Fire, Earth, Metal, Water).
        element2: The second element.
    """
    interactions = {
        ("Wood", "Fire"): "Generating (Wood feeds Fire)",
        ("Fire", "Earth"): "Generating (Fire creates Earth)",
        ("Earth", "Metal"): "Generating (Earth bears Metal)",
        ("Metal", "Water"): "Generating (Metal holds Water)",
        ("Water", "Wood"): "Generating (Water nourishes Wood)",
        ("Wood", "Earth"): "Controlling (Wood parts Earth)",
        ("Earth", "Water"): "Controlling (Earth dams Water)",
        ("Water", "Fire"): "Controlling (Water extinguishes Fire)",
        ("Fire", "Metal"): "Controlling (Fire melts Metal)",
        ("Metal", "Wood"): "Controlling (Metal chops Wood)",
    }
    
    e1 = element1.capitalize()
    e2 = element2.capitalize()
    
    if e1 == e2: return f"Harmony (Same element: {e1})"
    return interactions.get((e1, e2), interactions.get((e2, e1), "Neutral or Unknown relationship"))

@tool(parse_docstring=True)
def calculate_score(positive_factors: List[str], negative_factors: List[str]) -> str:
    """Calculate a favorability score based on positive and negative factors.

    Args:
        positive_factors: List of positive symbols or factors identified.
        negative_factors: List of negative symbols or factors identified.
    """
    pos_count = len(positive_factors)
    neg_count = len(negative_factors)
    total = pos_count + neg_count
    
    if total == 0: return "No factors provided for scoring."
    
    favorable_pct = int((pos_count / total) * 100)
    unfavorable_pct = 100 - favorable_pct
    
    # Simple logic for now, can be enhanced
    if favorable_pct >= 70: strength = "Strong"
    elif favorable_pct >= 50: strength = "Moderate"
    else: strength = "Weak"
    
    return f"""**Probability Assessment:**
- Favorable: {favorable_pct}%
- Unfavorable: {unfavorable_pct}%
- Strength: {strength}
"""
