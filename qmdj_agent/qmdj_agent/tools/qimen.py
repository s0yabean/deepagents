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

def _get_palace_data(palaces, palace_num: int) -> Optional[Dict]:
    """Helper to handle palaces stored as either a dictionary or a list."""
    if isinstance(palaces, list):
        if 0 <= palace_num < len(palaces):
            return palaces[palace_num]
    elif isinstance(palaces, dict):
        # Try string key first, then int key
        res = palaces.get(str(palace_num))
        if res is None:
            res = palaces.get(palace_num)
        return res
    return None

def find_palaces_with_stem(chart_data: dict, stem: str) -> List[int]:
    """Find which palaces contain the given heaven stem by searching the chart."""
    palaces = chart_data.get("palaces", {})
    found_palaces = []
    for palace_num in range(1, 10):
        palace_data = _get_palace_data(palaces, palace_num) or {}
        heaven_stem = palace_data.get("heaven_stem", "")
        if stem in heaven_stem:
            found_palaces.append(palace_num)
    return found_palaces

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

def find_palace_of_symbol(chart_data: dict, symbol: str) -> int:
    """Find which palace contains the given symbol (Door, Star, Deity, or Stem)."""
    palaces = chart_data.get("palaces", {})
    # Normalize if possible
    symbol = NORMALIZE_MAP.get(symbol, symbol)
    
    for palace_num in range(1, 10):
        p = _get_palace_data(palaces, palace_num) or {}
        # Check all symbol fields
        if symbol == p.get("door") or \
           symbol == p.get("star") or \
           symbol == p.get("deity") or \
           symbol in p.get("heaven_stem", "") or \
           symbol == p.get("earth_stem"):
            return palace_num
    return 0

def get_symbol_element(symbol_name: str) -> str:
    """Retrieve the Five Element association for a given symbol name."""
    key = NORMALIZE_MAP.get(symbol_name, symbol_name)
    data = SYMBOL_DATA.get(key)
    if not data:
        # Try suffixes
        if key + "门" in SYMBOL_DATA: data = SYMBOL_DATA[key + "门"]
        elif key + "星" in SYMBOL_DATA: data = SYMBOL_DATA[key + "星"]
    
    return data.get("element", "Unknown") if data else "Unknown"

@tool(parse_docstring=True)
def calculate_box_energy(chart_json: str) -> str:
    """Calculate energy levels for all 9 palaces based on Death/Emptiness, Tai Sui, and overflow.

    The input chart_json MUST follow this structure:
    {
        "gan_zhi": {"year": "乙巳"},  # Year Stem+Branch (2 chars)
        "palaces": { 
            "1": { "heaven_stem": "...", "door": "...", ... }, 
            # OR as a list: [null, {palace1_data}, {palace2_data}, ...]
            ... 
        },
        "empty_death": "..."
    }
    
    Args:
        chart_json: JSON string from qmdj_chart_api containing chart data.
    """
    try:
        chart = json.loads(chart_json)
        
        # Step 1: Extract year stem and branch
        year_ganzhi = chart.get("gan_zhi", {}).get("year", "")
        if len(year_ganzhi) != 2:
            return json.dumps({
                "error": "Invalid year gan_zhi format. Expected 2 characters (Stem+Branch).",
                "received": year_ganzhi,
                "expected_format_example": {"gan_zhi": {"year": "乙巳"}}
            }, ensure_ascii=False)
        
        year_stem = year_ganzhi[0]
        year_branch = year_ganzhi[1]
        
        # Step 2: Find palaces for year stem and branch
        tai_sui_palaces = set()
        year_stem_palaces = find_palaces_with_stem(chart, year_stem)
        year_branch_palace = get_palace_for_branch(year_branch)
        
        for p in year_stem_palaces: tai_sui_palaces.add(p)
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
        
        # Step 6: Apply Tai Sui boost (increase to 150%, or 100% if in DE)
        for palace in tai_sui_palaces:
            current = energy_data[str(palace)]["energy"]
            if current == 20:
                energy_data[str(palace)]["energy"] = 100
                energy_data[str(palace)]["modifier"].append("tai_sui_override")
                energy_data[str(palace)]["details"].append(f"Tai Sui boost: 20% → 100%")
            else:
                energy_data[str(palace)]["energy"] = 150
                energy_data[str(palace)]["modifier"].append("tai_sui")
                energy_data[str(palace)]["details"].append(f"Tai Sui boost: 100% → 150%")
        
        # Step 7: Apply diagonal overflow
        overflow_json = detect_diagonal_overflow.invoke({"chart_json": chart_json})
        overflow_info = json.loads(overflow_json)
        if overflow_info.get("overflow_detected"):
            for palace_num in overflow_info.get("affected_palaces", []):
                palace_str = str(palace_num)
                if palace_num not in tai_sui_palaces:
                    if palace_num in de_palaces:
                        energy_data[palace_str]["energy"] = 100
                        energy_data[palace_str]["modifier"].append("overflow_from_tai_sui")
                        energy_data[palace_str]["details"].append(f"Diagonal overflow from Tai Sui: 20% → 100%")
                    else:
                        energy_data[palace_str]["energy"] = 150
                        energy_data[palace_str]["modifier"].append("overflow_from_tai_sui")
                        energy_data[palace_str]["details"].append(f"Diagonal overflow from Tai Sui: 100% → 150%")
        
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
    """Apply Tai Sui year-based energy modifiers.
    
    Args:
        energy_json: JSON string with energy data.
        year: The year to apply modifiers for.
    """
    try:
        energy_data = json.loads(energy_json)
        # Simple year-based logic: Years ending in 0, 2, 4, 6, 8 are Yang years (stronger)
        # This is a placeholder for more complex Tai Sui logic
        is_yang_year = (year % 2 == 0)
        energy_data["year_type"] = "Yang" if is_yang_year else "Yin"
        energy_data["tai_sui_applied"] = True
        return json.dumps(energy_data, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Tai Sui calculation failed: {str(e)}"})

@tool(parse_docstring=True)
def detect_diagonal_overflow(chart_json: str) -> str:
    """Detect diagonal overflow patterns from Tai Sui palaces.
    
    Args:
        chart_json: JSON string containing chart data.
    """
    try:
        chart = json.loads(chart_json)
        year_ganzhi = chart.get("gan_zhi", {}).get("year", "")
        if not year_ganzhi: return json.dumps({"overflow_detected": False})
        
        year_stem = year_ganzhi[0]
        year_branch = year_ganzhi[1]
        
        tai_sui_palaces = set()
        year_stem_palaces = find_palaces_with_stem(chart, year_stem)
        year_branch_palace = get_palace_for_branch(year_branch)
        
        for p in year_stem_palaces: tai_sui_palaces.add(p)
        if year_branch_palace: tai_sui_palaces.add(year_branch_palace)
        
        # Identify Death/Emptiness palaces
        empty_death_str = chart.get("empty_death", "")
        de_palaces = set()
        for char in empty_death_str:
            palace = get_palace_for_branch(char)
            if palace: de_palaces.add(palace)
        
        affected_palaces = []
        for ts_palace in tai_sui_palaces:
            # Skip overflow if Tai Sui palace is also in Death/Emptiness
            if ts_palace in de_palaces:
                continue
                
            diagonal = get_diagonal_palace(ts_palace)
            if diagonal and diagonal not in tai_sui_palaces:
                affected_palaces.append(diagonal)
        
        return json.dumps({
            "overflow_detected": len(affected_palaces) > 0,
            "affected_palaces": sorted(list(set(affected_palaces))),
            "tai_sui_palaces": sorted(list(tai_sui_palaces)),
            "de_palaces": sorted(list(de_palaces))
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Overflow detection failed: {str(e)}"})

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
    "值符": "值符",
    "蛇": "腾蛇",
    "腾蛇": "腾蛇",
    "螣蛇": "腾蛇",
    "陰": "太阴", # Traditional 'Yin'
    "阴": "太阴", # Simplified 'Yin' abbr
    "太陰": "太阴", # Traditional Full
    "太阴": "太阴",
    "合": "六合",
    "六合": "六合",
    "虎": "白虎",
    "白虎": "白虎",
    "玄": "玄武",
    "玄武": "玄武",
    "地": "九地",
    "九地": "九地",
    "天": "九天", # 'Heaven' abbr for Nine Heavens
    "九天": "九天",
}

PALACE_ELEMENTS = {
    1: "Water",
    2: "Earth",
    3: "Wood",
    4: "Wood",
    5: "Earth",
    6: "Metal",
    7: "Metal",
    8: "Earth",
    9: "Fire"
}

SYMBOL_DATA = {
    # ========== 8 Doors (八门) ==========
    "休门": {"name_en": "Rest Door", "pinyin": "Xiu Men", "element": "Water", "general": "Relaxation, recovery, family, nobility.", "recommendation": "Take a step back to rest. Focus on internal matters."},
    "生门": {"name_en": "Life Door", "pinyin": "Sheng Men", "element": "Earth", "general": "Growth, profit, vitality, new beginnings.", "recommendation": "Actively pursue growth and profit. Launch new projects."},
    "伤门": {"name_en": "Injury Door", "pinyin": "Shang Men", "element": "Wood", "general": "Harm, hunting, gambling, debt collection.", "recommendation": "Be cautious of injury. Good for aggressive tasks like debt collection."},
    "杜门": {"name_en": "Delusion Door", "pinyin": "Du Men", "element": "Wood", "general": "Hiding, obstruction, secrecy, technical skills.", "recommendation": "Keep a low profile. Focus on research or technical work."},
    "景门": {"name_en": "View Door", "pinyin": "Jing Men", "element": "Fire", "general": "Beauty, documents, reputation, strategy.", "recommendation": "Focus on branding and reputation. Create a strategy."},
    "死门": {"name_en": "Death Door", "pinyin": "Si Men", "element": "Earth", "general": "Endings, stagnation, mourning, land.", "recommendation": "Accept endings. Do not start anything new. Good for land matters."},
    "惊门": {"name_en": "Fear Door", "pinyin": "Jing Men", "element": "Metal", "general": "Fear, disputes, lawsuits, panic.", "recommendation": "Prepare for disputes. Use your voice for debate."},
    "开门": {"name_en": "Open Door", "pinyin": "Kai Men", "element": "Metal", "general": "Career, opportunity, opening, public.", "recommendation": "Seize the opportunity. Open new doors in career and business."},

    # ========== 9 Stars (九星) ==========
    "天蓬": {"name_en": "Grass Star (Robber Star)", "pinyin": "Tian Peng", "element": "Water", "general": "Risk taking, intelligence, loss of wealth.", "recommendation": "Take calculated risks but secure your assets."},
    "天芮": {"name_en": "Grain Star (Problem Star)", "pinyin": "Tian Rui", "element": "Earth", "general": "Illness, problems, learning, students.", "recommendation": "Identify and fix internal problems. Focus on learning."},
    "天冲": {"name_en": "Impulse Star", "pinyin": "Tian Chong", "element": "Wood", "general": "Action, impulse, charity, sports.", "recommendation": "Take quick, decisive action. Avoid overthinking."},
    "天辅": {"name_en": "Assistant Star", "pinyin": "Tian Fu", "element": "Wood", "general": "Education, assistance, culture, nobility.", "recommendation": "Seek help from mentors. Focus on education."},
    "天禽": {"name_en": "Bird Star", "pinyin": "Tian Qin", "element": "Earth", "general": "Central, reliable, honest.", "recommendation": "Lead with honesty and reliability."},
    "天心": {"name_en": "Doctor Star", "pinyin": "Tian Xin", "element": "Metal", "general": "Leadership, authority, medical matters.", "recommendation": "Take charge and plan strategically. Focus on healing."},
    "天柱": {"name_en": "Destroyer Star", "pinyin": "Tian Zhu", "element": "Metal", "general": "Support, legal matters, rigidity.", "recommendation": "Stand firm on principles but avoid rigidity."},
    "天任": {"name_en": "Diplomat Star", "pinyin": "Tian Ren", "element": "Earth", "general": "Wealth, responsibility, real estate.", "recommendation": "Be patient and responsible. Focus on long-term wealth."},
    "天英": {"name_en": "Hero Star", "pinyin": "Tian Ying", "element": "Fire", "general": "Brightness, fame, passion, beauty.", "recommendation": "Seek fame and recognition. Be careful of burnout."},

    # ========== 8 Deities (八神) ==========
    "值符": {"name_en": "Chief", "pinyin": "Zhi Fu", "element": "Earth", "general": "The leader, protection, wealth, high status.", "recommendation": "Take the lead with confidence. You are protected."},
    "腾蛇": {"name_en": "Snake", "pinyin": "Teng She", "element": "Fire", "general": "Deception, hypocrisy, supernatural, changing.", "recommendation": "Be vigilant against deception. Adapt to changes."},
    "太阴": {"name_en": "Moon", "pinyin": "Tai Yin", "element": "Metal", "general": "Secrets, planning, darkness, female help.", "recommendation": "Plan in secret. Seek assistance from women."},
    "六合": {"name_en": "Six Harmony", "pinyin": "Liu He", "element": "Wood", "general": "Relationships, marriage, partnership, negotiation.", "recommendation": "Focus on networking and partnerships."},
    "白虎": {"name_en": "White Tiger", "pinyin": "Bai Hu", "element": "Metal", "general": "Ferocity, injury, blood, pressure.", "recommendation": "Prepare for high pressure. Avoid confrontation."},
    "玄武": {"name_en": "Black Tortoise", "pinyin": "Xuan Wu", "element": "Water", "general": "Theft, deception, loss, secrets.", "recommendation": "Guard your assets. Watch out for theft and fraud."},
    "九地": {"name_en": "Nine Earth", "pinyin": "Jiu Di", "element": "Earth", "general": "Stability, slowness, long-term, hiding.", "recommendation": "Adopt a low profile. Think long-term."},
    "九天": {"name_en": "Nine Heavens", "pinyin": "Jiu Tian", "element": "Metal", "general": "Active, fast, travel, high ambition.", "recommendation": "Aim high and move fast. Expand your horizons."},

    # ========== 10 Stems (十干) ==========
    "甲": {"name_en": "Yang Wood", "pinyin": "Jia", "element": "Wood", "general": "Noble person, leadership, the best.", "recommendation": "Act as a leader. Strive for excellence."},
    "乙": {"name_en": "Yin Wood", "pinyin": "Yi", "element": "Wood", "general": "Women, winding path, artistic, flexibility.", "recommendation": "Be flexible and adaptable. Use soft skills."},
    "丙": {"name_en": "Yang Fire", "pinyin": "Bing", "element": "Fire", "general": "Transformation, chaos, breakthrough.", "recommendation": "Create a breakthrough. Be decisive."},
    "丁": {"name_en": "Yin Fire", "pinyin": "Ding", "element": "Fire", "general": "Hope, documents, contracts, inspiration.", "recommendation": "Focus on documents and details. Look for hope."},
    "戊": {"name_en": "Yang Earth", "pinyin": "Wu", "element": "Earth", "general": "Capital, finance, assets, trust.", "recommendation": "Manage your capital. Be reliable."},
    "己": {"name_en": "Yin Earth", "pinyin": "Ji", "element": "Earth", "general": "Desire, plan, scheme, hidden resources.", "recommendation": "Plan strategically. Keep resources hidden."},
    "庚": {"name_en": "Yang Metal", "pinyin": "Geng", "element": "Metal", "general": "Enemy, competitor, lawsuit, obstacles.", "recommendation": "Prepare for competition. Overcome obstacles."},
    "辛": {"name_en": "Yin Metal", "pinyin": "Xin", "element": "Metal", "general": "Mistake, problem, crime, refinement.", "recommendation": "Correct mistakes. Refine your approach."},
    "壬": {"name_en": "Yang Water", "pinyin": "Ren", "element": "Water", "general": "Journey, movement, change, flow.", "recommendation": "Go with the flow. Adapt to changes."},
    "癸": {"name_en": "Yin Water", "pinyin": "Gui", "element": "Water", "general": "Network, relationship, communication.", "recommendation": "Leverage your network. Communicate discreetly."},

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

SYMBOL_QUALITY = {
    # Doors
    "休门": 1, "生门": 1, "开门": 1,
    "景门": 0, "杜门": 0,
    "伤门": -1, "死门": -1, "惊门": -1,
    # Stars
    "天辅": 1, "天任": 1, "天心": 1, "天禽": 1,
    "天冲": 0, "天英": 0,
    "天蓬": -1, "天芮": -1, "天柱": -1,
    # Deities
    "值符": 1, "太阴": 1, "六合": 1, "九地": 1, "九天": 1,
    "腾蛇": 0,
    "白虎": -1, "玄武": -1
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
        if key + "门" in SYMBOL_DATA: data = SYMBOL_DATA[key + "门"]
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
    
    Covers Generating (生), Draining (泄), Controlling (克), and Weakening (耗) cycles.

    Args:
        element1: The first element (Wood, Fire, Earth, Metal, Water).
        element2: The second element.
    """
    e1 = element1.capitalize()
    e2 = element2.capitalize()
    
    if e1 == e2: return f"Harmony (Same element: {e1})"
    
    # Generating Cycle: Wood -> Fire -> Earth -> Metal -> Water -> Wood
    generating = {
        "Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"
    }
    
    # Controlling Cycle: Wood -> Earth -> Water -> Fire -> Metal -> Wood
    controlling = {
        "Wood": "Earth", "Earth": "Water", "Water": "Fire", "Fire": "Metal", "Metal": "Wood"
    }
    
    if generating.get(e2) == e1:
        return f"Generating ({e1} is generated by {e2})"
    if generating.get(e1) == e2:
        return f"Draining ({e1} is drained by {e2})"
    if controlling.get(e1) == e2:
        return f"Controlling ({e1} overcomes {e2})"
    if controlling.get(e2) == e1:
        return f"Weakening ({e1} is weakened by {e2})"
        
    return f"Neutral relationship between {e1} and {e2}"

@tool(parse_docstring=True)
def calculate_score(palace_num: int, chart_json: str, energy_json: str) -> str:
    """Calculate a favorability score for a specific palace based on symbols, elements, and energy.

    Args:
        palace_num: The palace number to evaluate (1-9).
        chart_json: JSON string containing the full chart data.
        energy_json: JSON string containing the energy analysis data.
    """
    try:
        chart = json.loads(chart_json)
        energy_data = json.loads(energy_json)
    except Exception as e:
        return f"Error parsing data: {str(e)}"

    palaces = chart.get("palaces", {})
    p = _get_palace_data(palaces, palace_num)
    if not p: return f"Palace {palace_num} not found in chart."

    palace_element = PALACE_ELEMENTS.get(palace_num, "Unknown")
    
    # Base Score
    score = 50.0
    details = []

    # Evaluate Symbols
    symbols = [p.get("door"), p.get("star"), p.get("deity")]
    # Stems are more complex, but we can add them if they are in SYMBOL_QUALITY
    # For now focus on Door, Star, Deity
    
    weights = {"door": 20, "star": 15, "deity": 15}
    
    for s_type in ["door", "star", "deity"]:
        s_name = p.get(s_type)
        if not s_name: continue
        
        # Quality Points
        quality = SYMBOL_QUALITY.get(s_name, 0)
        q_points = quality * weights[s_type]
        score += q_points
        if q_points != 0:
            details.append(f"{s_name} ({s_type}): {'+' if q_points > 0 else ''}{q_points} quality")
            
        # Elemental Interaction Points
        s_elem = get_symbol_element(s_name)
        if s_elem != "Unknown" and palace_element != "Unknown":
            interaction = five_element_interaction.invoke({"element1": s_elem, "element2": palace_element})
            i_points = 0
            if "Generating" in interaction: i_points = 10
            elif "Harmony" in interaction: i_points = 5
            elif "Draining" in interaction: i_points = -5
            elif "Controlling" in interaction or "Weakening" in interaction: i_points = -10
            
            score += i_points
            if i_points != 0:
                details.append(f"{s_name} vs Palace ({palace_element}): {'+' if i_points > 0 else ''}{i_points} interaction")

    # Clamp score before energy scaling
    score = max(0, min(100, score))
    
    # Energy Scaling
    energy_pct = 100
    p_energy_data = _get_palace_data(energy_data, palace_num)
    if isinstance(p_energy_data, dict):
        energy_pct = p_energy_data.get("energy", 100)
    elif isinstance(p_energy_data, (int, float)):
        energy_pct = p_energy_data
    elif isinstance(energy_data, (int, float)):
        energy_pct = energy_data

    final_score = int(score * (energy_pct / 100.0))
    
    # Strength Rating
    if final_score >= 80: strength = "Excellent"
    elif final_score >= 60: strength = "Good"
    elif final_score >= 40: strength = "Neutral/Moderate"
    elif final_score >= 20: strength = "Weak"
    else: strength = "Very Poor"

    return f"""**Palace {palace_num} Favorability Assessment:**
- **Final Score:** {final_score}/100
- **Rating:** {strength}
- **Palace Energy:** {energy_pct}%
- **Palace Element:** {palace_element}

**Scoring Breakdown:**
- Base Score: 50
{chr(10).join(['- ' + d for d in details])}
- Pre-Energy Total: {int(score)}
"""

@tool(parse_docstring=True)
def compare_palaces(palace_list: List[int], chart_json: str, energy_json: str) -> str:
    """Compare multiple palaces side-by-side based on their favorability scores.

    Args:
        palace_list: List of palace numbers (1-9) to compare.
        chart_json: JSON string containing the full chart data.
        energy_json: JSON string containing the energy analysis data.
    """
    results = []
    for p_num in palace_list:
        score_str = calculate_score.invoke({
            "palace_num": p_num,
            "chart_json": chart_json,
            "energy_json": energy_json
        })
        # Extract score and rating from the string
        lines = score_str.split("\n")
        score = "N/A"
        rating = "N/A"
        for line in lines:
            if "Final Score:" in line: score = line.split(":")[-1].strip()
            if "Rating:" in line: rating = line.split(":")[-1].strip()
        
        results.append(f"| Palace {p_num} | {score} | {rating} |")
    
    table = "\n".join([
        "| Palace | Score | Rating |",
        "| :--- | :--- | :--- |",
        *results
    ])
    
    return f"**Palace Comparison Table:**\n\n{table}"

@tool(parse_docstring=True)
def get_elemental_remedy(source_element: str, target_element: str) -> str:
    """Suggest a bridge element to resolve a controlling or weakening relationship.

    Args:
        source_element: The element that is controlling or being weakened.
        target_element: The element that is being controlled or is weakening the source.
    """
    # Bridge elements (Generating cycles)
    # Wood -> Fire -> Earth -> Metal -> Water -> Wood
    bridges = {
        ("Metal", "Wood"): "Water", # Metal controls Wood -> Use Water
        ("Wood", "Earth"): "Fire",  # Wood controls Earth -> Use Fire
        ("Earth", "Water"): "Metal", # Earth controls Water -> Use Metal
        ("Water", "Fire"): "Wood",  # Water controls Fire -> Use Wood
        ("Fire", "Metal"): "Earth", # Fire controls Metal -> Use Earth
        
        # Weakening (Draining in reverse)
        ("Wood", "Metal"): "Water", # Wood is controlled by Metal -> Use Water
        ("Earth", "Wood"): "Fire",  # Earth is controlled by Wood -> Use Fire
        ("Water", "Earth"): "Metal", # Water is controlled by Earth -> Use Metal
        ("Fire", "Water"): "Wood",  # Fire is controlled by Water -> Use Wood
        ("Metal", "Fire"): "Earth", # Metal is controlled by Fire -> Use Earth
    }
    
    remedy = bridges.get((source_element, target_element))
    if remedy:
        return f"To resolve the conflict between {source_element} and {target_element}, use the **{remedy}** element as a bridge. {source_element} generates {remedy}, and {remedy} generates {target_element}."
    
    return f"No specific bridge element needed for the relationship between {source_element} and {target_element}."


@tool(parse_docstring=True)
def verify_palace_attributes(palace_num: int, chart_json: str) -> str:
    """Verify exactly what is present in a specific palace to prevent hallucination.
    
    Args:
        palace_num: The palace number to check (1-9).
        chart_json: JSON string containing the full chart data.
    """
    try:
        chart = json.loads(chart_json)
        palaces = chart.get("palaces", {})
        p_data = _get_palace_data(palaces, palace_num)
        
        if not p_data:
            return f"❌ Palace {palace_num} data NOT FOUND."
            
        # Extract Markers (DE/Horse)
        markers = p_data.get("markers", [])
        is_empty = "空" in markers
        is_horse = "馬" in markers
        
        # Extract Symbols
        door = p_data.get("door", "None")
        star = p_data.get("star", "None")
        deity = p_data.get("deity", "None")
        stem_heaven = p_data.get("heaven_stem", "None")
        stem_earth = p_data.get("earth_stem", "None")
        
        # Get English Meanings
        # Helper to safely call symbol_lookup (which is a tool, so we call it directly as function here or handle str)
        # Since we are inside the same module, we can access SYMBOL_DATA directly for efficiency 
        # instead of invoking the tool wrapper which might add overhead.
        
        def get_meaning(sym):
            if sym == "None": return "None"
            # Normalize
            key = sym.strip()
            key = NORMALIZE_MAP.get(key, key)
            data = SYMBOL_DATA.get(key)
            if not data:
                # Try suffixes
                if key + "门" in SYMBOL_DATA: data = SYMBOL_DATA[key + "门"]
                elif key + "星" in SYMBOL_DATA: data = SYMBOL_DATA[key + "星"]
            
            if data:
                return f"{data.get('name_en', 'Unknown')} - {data.get('general', '')}"
            return "Unknown Symbol"

        door_info = get_meaning(door)
        star_info = get_meaning(star)
        deity_info = get_meaning(deity)
        
        # Format Verification Report
        report = [
            f"🔍 VERIFICATION REPORT FOR PALACE {palace_num}:",
            f"----------------------------------------",
            f"► ATTRIBUTES:",
            f"  • Door: {door} ({door_info})",
            f"  • Star: {star} ({star_info})",
            f"  • Deity: {deity} ({deity_info})",
            f"  • Stems: {stem_heaven} (Heaven) / {stem_earth} (Earth)",
            f"",
            f"► STATUS FLAGS (CRITICAL):",
            f"  • Is Empty/Void (空)? {'✅ YES' if is_empty else '❌ NO'}",
            f"  • Is Travelling Horse (馬)? {'✅ YES' if is_horse else '❌ NO'}",
            f"",
            f"► CONCLUSION:",
            f"  This palace is {'EMPTY/HOLLOW' if is_empty else 'SOLID (Not Empty)'}.",
            f"  It contains the {door} and {star}."
        ]
        
        return "\n".join(report)
        
    except Exception as e:
        return f"Error verifying palace: {str(e)}"

