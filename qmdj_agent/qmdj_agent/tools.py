from langchain_core.tools import tool
from typing import Dict, List, Optional
import json
from datetime import datetime
import httpx
from tavily import TavilyClient
from markdownify import markdownify
from qmdj_agent.chart_generator.qimen_generator import QimenGenerator

# ==============================================================================
# Time Utility Tools
# ==============================================================================

@tool(parse_docstring=True)
def get_current_time() -> str:
    """Get the current date and time in ISO 8601 format for chart generation.
    
    Use this tool to get the current timestamp before calling qmdj_chart_api.
    The returned time is in GMT+8 (Beijing Time).
    """
    now = datetime.now()
    return now.strftime("%Y-%m-%dT%H:%M:%S")

# ==============================================================================
# Web Search Tool (Context Advisor)
# ==============================================================================

def fetch_webpage_content(url: str, timeout: float = 10.0) -> str:
    """Fetch and convert webpage content to markdown."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
        html_content = response.text
        markdown_content = markdownify(html_content, heading_style="ATX")
        # Limit content length
        return markdown_content[:3000] if len(markdown_content) > 3000 else markdown_content
    except Exception as e:
        return f"Error fetching content: {str(e)}"

@tool(parse_docstring=True)
def tavily_search(query: str, max_results: int = 2) -> str:
    """Search the web for information to provide external context and evidence.
    
    Use this to find real-world data, news, trends, or research that relates to
    the user's question. This grounds QMDJ readings with objective evidence.
    
    Args:
        query: Search query to execute
        max_results: Maximum number of results to return (default: 2)
    """
    try:
        # Lazy initialization of Tavily client (only when search is called)
        tavily_client = TavilyClient()
        
        # Use Tavily to discover URLs
        search_results = tavily_client.search(
            query,
            max_results=max_results,
            topic="general"
        )
        
        # Fetch full content for each URL
        result_texts = []
        for result in search_results.get("results", []):
            url = result["url"]
            title = result["title"]
            
            # Fetch webpage content
            content = fetch_webpage_content(url)
            
            result_text = f"""## {title}
**URL:** {url}

{content}

---
"""
            result_texts.append(result_text)
        
        # Format final response
        response = f"""🔍 Found {len(result_texts)} result(s) for '{query}':

{chr(10).join(result_texts)}"""
        
        return response
    except Exception as e:
        return f"Search error: {str(e)}. Please try a different query."

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
# Energy Analysis Tools (Energy Analyzer Specialist)
# ==============================================================================


# Helper functions for energy calculation
def find_palace_with_stem(chart_data: dict, stem: str) -> int:
    """Find which palace contains the given heaven stem by searching the chart.
    
    Args:
        chart_data: The full chart dictionary from qmdj_chart_api
        stem: The heaven stem to search for (e.g., '乙')
    
    Returns:
        Palace number (1-9) or 0 if not found
    """
    palaces = chart_data.get("palaces", {})
    for palace_num in range(1, 10):
        palace_data = palaces.get(str(palace_num), {})
        heaven_stem = palace_data.get("heaven_stem", "")
        # Check if this palace contains the stem (might have multiple stems)
        if stem in heaven_stem:
            return palace_num
    return 0


def get_palace_for_branch(branch: str) -> int:
    """Map earthly branch (zodiac) to palace number.
    
    Box 1: 子 (Rat)
    Box 2: 未 (Goat), 申 (Monkey)
    Box 3: 卯 (Rabbit)
    Box 4: 巳 (Snake), 辰 (Dragon)
    Box 5: Nothing (center/pivot)
    Box 6: 戌 (Dog), 亥 (Pig)
    Box 7: 酉 (Rooster)
    Box 8: 寅 (Tiger), 丑 (Ox)
    Box 9: 午 (Horse)
    """
    branch_to_palace = {
        "子": 1,  # Rat
        "未": 2,  # Goat
        "申": 2,  # Monkey
        "卯": 3,  # Rabbit
        "辰": 4,  # Dragon
        "巳": 4,  # Snake
        "戌": 6,  # Dog
        "亥": 6,  # Pig
        "酉": 7,  # Rooster
        "丑": 8,  # Ox
        "寅": 8,  # Tiger
        "午": 9,  # Horse
    }
    return branch_to_palace.get(branch, 0)

def get_diagonal_palace(palace: int) -> int:
    """Get diagonal opposite palace. Palace 5 (center) has no diagonal."""
    diagonal_map = {1: 9, 2: 8, 3: 7, 4: 6, 6: 4, 7: 3, 8: 2, 9: 1, 5: 0}
    return diagonal_map.get(palace, 0)

@tool(parse_docstring=True)
def calculate_box_energy(chart_json: str) -> str:
    """Calculate energy levels for all 9 palaces based on Death/Emptiness, Tai Sui, and overflow.
    
    Logic:
    1. All palaces start at 100% energy
    2. Death/Emptiness (DE) reduces palace to 20%
    3. Tai Sui (year stem/branch palaces) boost to 150%
    4. Diagonal overflow from Tai Sui palaces:
       - If diagonal has no DE: 150%
       - If diagonal has DE: 100% (boosted from 20%)
    
    Args:
        chart_json: JSON string from qmdj_chart_api containing chart data
    """
    try:
        chart = json.loads(chart_json)
        
        # Step 1: Extract year stem and branch
        year_ganzhi = chart.get("gan_zhi", {}).get("year", "")
        if len(year_ganzhi) != 2:
            return json.dumps({"error": "Invalid year gan_zhi format"})
        
        year_stem = year_ganzhi[0]  # 乙
        year_branch = year_ganzhi[1]  # 巳
        
        # Step 2: Find palaces for year stem and branch (dynamically from chart)
        tai_sui_palaces = set()
        year_stem_palace = find_palace_with_stem(chart, year_stem)
        year_branch_palace = get_palace_for_branch(year_branch)
        
        if year_stem_palace:
            tai_sui_palaces.add(year_stem_palace)
        if year_branch_palace:
            tai_sui_palaces.add(year_branch_palace)
        
        # Step 3: Identify Death/Emptiness palaces
        empty_death_str = chart.get("empty_death", "")  # e.g., "申酉"
        de_palaces = set()
        
        for char in empty_death_str:
            palace = get_palace_for_branch(char)
            if palace:
                de_palaces.add(palace)
        
        # Step 4: Initialize all palaces at 100%
        energy_data = {}
        for i in range(1, 10):
            energy_data[str(i)] = {
                "energy": 100,
                "modifier": [],
                "details": []
            }
        
        # Step 5: Apply Death/Emptiness (reduce to 20%)
        for palace in de_palaces:
            energy_data[str(palace)]["energy"] = 20
            energy_data[str(palace)]["modifier"].append("death_emptiness")
            energy_data[str(palace)]["details"].append("Death/Emptiness: 100% → 20%")
        
        # Step 6: Apply Tai Sui boost (increase to 150%)
        for palace in tai_sui_palaces:
            current = energy_data[str(palace)]["energy"]
            if current == 20:  # Had DE
                energy_data[str(palace)]["energy"] = 150
                energy_data[str(palace)]["modifier"].append("tai_sui_override")
                energy_data[str(palace)]["details"].append(f"Tai Sui boost: 20% → 150%")
            else:  # Normal
                energy_data[str(palace)]["energy"] = 150
                energy_data[str(palace)]["modifier"].append("tai_sui")
                energy_data[str(palace)]["details"].append(f"Tai Sui boost: 100% → 150%")
        
        # Step 7: Apply diagonal overflow from Tai Sui palaces
        for tai_sui_palace in tai_sui_palaces:
            diagonal = get_diagonal_palace(tai_sui_palace)
            if diagonal == 0:  # Center palace (5) has no diagonal
                continue
            
            diagonal_str = str(diagonal)
            # Only apply overflow if the diagonal palace hasn't already been boosted by Tai Sui directly
            if diagonal not in tai_sui_palaces:
                if diagonal in de_palaces:
                    # Diagonal has DE: boost from 20% to 100%
                    energy_data[diagonal_str]["energy"] = 100
                    energy_data[diagonal_str]["modifier"].append("overflow_from_tai_sui")
                    energy_data[diagonal_str]["details"].append(
                        f"Diagonal overflow from Palace {tai_sui_palace} (Tai Sui): 20% → 100%"
                    )
                else:
                    # Diagonal is clean: boost to 150%
                    energy_data[diagonal_str]["energy"] = 150
                    energy_data[diagonal_str]["modifier"].append("overflow_from_tai_sui")
                    energy_data[diagonal_str]["details"].append(
                        f"Diagonal overflow from Palace {tai_sui_palace} (Tai Sui): 100% → 150%"
                    )
        
        # Step 8: Convert modifiers to strings for JSON
        for palace_key in energy_data:
            if not energy_data[palace_key]["modifier"]:
                energy_data[palace_key]["modifier"] = "normal"
            else:
                energy_data[palace_key]["modifier"] = ", ".join(energy_data[palace_key]["modifier"])
        
        # Add summary
        energy_data["summary"] = {
            "year_ganzhi": year_ganzhi,
            "year_stem": year_stem,
            "year_branch": year_branch,
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
    """Apply Tai Sui year-based energy modifiers (DEPRECATED - now built into calculate_box_energy).
    
    Tai Sui logic is now integrated directly into calculate_box_energy.
    This function is kept for backward compatibility.
    
    Args:
        energy_json: JSON from calculate_box_energy
        year: Year to calculate Tai Sui for
    """
    # STUB: To be implemented
    try:
        energy_data = json.loads(energy_json)
        energy_data["tai_sui_applied"] = f"Year {year} (STUB: Not yet implemented)"
        return json.dumps(energy_data, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Tai Sui calculation failed: {str(e)}"})

@tool(parse_docstring=True)
def detect_diagonal_overflow(chart_json: str) -> str:
    """Detect diagonal overflow patterns where Death/Emptiness causes energy redistribution.
    
    When a palace has DE, its diagonal opposite gains overflow energy.
    
    Args:
        chart_json: JSON string from qmdj_chart_api
    """
    # STUB: To be implemented
    # Diagonal pairs: 1-9, 2-8, 3-7, 4-6 (5 has no diagonal)
    return json.dumps({
        "overflow_detected": False,
        "affected_palaces": [],
        "note": "STUB: Diagonal overflow detection not yet implemented"
    }, ensure_ascii=False, indent=2)

# ==============================================================================
# QMDJ Knowledge Base Tools
# ==============================================================================

# Comprehensive Symbol Database with Recommendations
SYMBOL_DATA = {
    # ========== 8 Doors (八門) ==========
    "休門": {
        "general": "Rest Door (Xiu Men). Water element. Relaxation, recovery, family, nobility.",
        "business": "Good for meetings, negotiations, personnel matters, and taking a break. Not good for aggressive expansion.",
        "relationship": "Harmonious, peaceful, family-oriented. Good for marriage and reconciliation.",
        "health": "Recovery, healing, rest. Good for treating illness.",
        "recommendation": "Take a step back to rest and recover. Focus on internal matters, family, and personnel harmony rather than aggressive action."
    },
    "生門": {
        "general": "Life Door (Sheng Men). Earth element. Growth, profit, vitality, new beginnings. The most auspicious door.",
        "business": "Excellent for starting businesses, seeking profit, investment, and expansion. Financial gain.",
        "relationship": "Growth, new relationships, fertility. Positive development.",
        "health": "Vitality, recovery, life energy. Excellent for health.",
        "recommendation": "Actively pursue growth and profit. Launch new projects, invest, and expand. The energy supports new beginnings."
    },
    "傷門": {
        "general": "Injury Door (Shang Men). Wood element. Harm, hunting, gambling, debt collection. Aggressive energy.",
        "business": "Good for collecting debts, competitive sports, or hunting. Bad for construction or travel. Risk of injury or loss.",
        "relationship": "Conflict, hurt feelings, aggressive pursuit. Potential for emotional pain.",
        "health": "Injury, surgery, physical trauma. Caution required.",
        "recommendation": "Be cautious of injury or conflict. Good for aggressive tasks like debt collection or sports, but avoid travel or starting peaceful ventures."
    },
    "杜門": {
        "general": "Delusion Door (Du Men). Wood element. Hiding, obstruction, secrecy, technical skills.",
        "business": "Good for hiding assets, research, technical work, or escaping. Bad for public announcements or seeking help.",
        "relationship": "Secrets, hidden feelings, blockage. Communication breakdown.",
        "health": "Blockages, clots, hidden illnesses. Hard to diagnose.",
        "recommendation": "Keep a low profile and protect your secrets. Focus on research or technical work. Avoid public exposure."
    },
    "景門": {
        "general": "View Door (Jing Men). Fire element. Beauty, documents, reputation, strategy. Brightness.",
        "business": "Good for advertising, branding, legal documents, and strategy. Watch out for superficiality.",
        "relationship": "Attraction, superficial beauty, passionate but potentially short-lived.",
        "health": "Blood, heart, eyes. Inflammation.",
        "recommendation": "Focus on branding, reputation, and paperwork. Create a strategy or plan. Be careful of style over substance."
    },
    "死門": {
        "general": "Death Door (Si Men). Earth element. Endings, stagnation, mourning, land. The most inauspicious door.",
        "business": "Bad for almost everything except hunting, funerals, or land measurement. Stagnation and obstacles.",
        "relationship": "End of relationship, coldness, stagnation. No growth.",
        "health": "Death, chronic illness, necrosis. Very negative.",
        "recommendation": "Accept endings and cut your losses. Do not start anything new. Good only for ending things or dealing with land/burial matters."
    },
    "驚門": {
        "general": "Fear Door (Jing Men). Metal element. Fear, disputes, lawsuits, panic. Loud noise.",
        "business": "Lawsuits, arguments, public speaking (debate). Chaos and panic. Good for lawyers.",
        "relationship": "Arguments, fear, anxiety. Verbal conflict.",
        "health": "Respiratory issues, anxiety, panic attacks. Lung problems.",
        "recommendation": "Prepare for disputes or legal challenges. Use your voice for debate, but be wary of anxiety and conflict."
    },
    "開門": {
        "general": "Open Door (Kai Men). Metal element. Career, opportunity, opening, public. Very auspicious.",
        "business": "Excellent for career advancement, opening new business, public office, and travel. Success.",
        "relationship": "Open communication, new opportunities. Public relationship.",
        "health": "Surgery (opening), recovery, lungs. Good for treatment.",
        "recommendation": "Seize the opportunity and move forward. Open new doors in career and business. Publicize your plans."
    },

    # ========== 9 Stars (九星) ==========
    "天蓬": {
        "general": "Heavenly Grass (Robber Star). Water. Risk taking, intelligence, loss of wealth. Great wisdom but potential for theft.",
        "business": "High risk ventures, speculation. Risk of theft or loss. Needs careful management.",
        "relationship": "Intelligent but potentially unfaithful or risky partner. Sexual attraction.",
        "health": "Kidney, ear, blood issues. Water-related illness.",
        "recommendation": "Take calculated risks but secure your assets. Good for bold, unconventional moves, but guard against loss."
    },
    "天芮": {
        "general": "Heavenly Grain (Problem/Student Star). Earth. Illness, problems, learning, students. The star of disease.",
        "business": "Problems, defects, internal issues. Good for education and learning (student).",
        "relationship": "Problematic relationship, nagging. Learning together.",
        "health": "Illness, disease, reproductive issues. Indicates health problems.",
        "recommendation": "Identify and fix internal problems. Focus on learning and education. Pay close attention to health issues."
    },
    "天冲": {
        "general": "Heavenly Impulse (Impulse Star). Wood. Action, impulse, charity, sports. Fast moving.",
        "business": "Fast action, sales, sports. Impulsive decisions may lead to regret. Good for charity.",
        "relationship": "Impulsive, quick romance. Action-oriented.",
        "health": "Liver, legs, injury from speed.",
        "recommendation": "Take quick, decisive action. Good for sales or sports. Avoid overthinking, but be careful of recklessness."
    },
    "天辅": {
        "general": "Heavenly Assistant (Advisor Star). Wood. Education, assistance, culture, nobility. Helpful people.",
        "business": "Education, training, seeking help, cultural arts. Good for exams and hiring.",
        "relationship": "Supportive, cultured partner. Mentorship.",
        "health": "Liver, wind issues. Generally good.",
        "recommendation": "Seek help from mentors or advisors. Focus on education, training, and cultural pursuits. Good for networking."
    },
    "天禽": {
        "general": "Heavenly Bird (Bird Star). Earth. Central, reliable, honest. The king of stars.",
        "business": "Leadership, reliability, central management. Honest dealings.",
        "relationship": "Honest, reliable partner. Central figure.",
        "health": "Spleen, stomach. General balance.",
        "recommendation": "Lead with honesty and reliability. Maintain a balanced, central position. Good for management."
    },
    "天心": {
        "general": "Heavenly Heart (Doctor Star). Metal. Leadership, authority, medical matters. Healing, planning, management.",
        "business": "Excellent for healthcare, finance, management, strategic planning. Leadership roles.",
        "relationship": "Caring, healing relationships. Emotional support.",
        "health": "Good for medical treatment and healing. Positive health outcomes.",
        "recommendation": "Take charge and plan strategically. Focus on healing and management. Consult a doctor or expert if needed."
    },
    "天柱": {
        "general": "Heavenly Pillar (Destroyer Star). Metal. Support, legal matters, but also rigidity. Destruction, arguments.",
        "business": "Legal support, structural matters, but inflexibility. Good for law, public speaking, entertainment.",
        "relationship": "Rigid structures, potential arguments. Communication challenges.",
        "health": "Structural health issues (bones, spine). Need for support.",
        "recommendation": "Stand firm on your principles but avoid being too rigid. Good for legal matters or breaking down old structures."
    },
    "天任": {
        "general": "Heavenly Responsibility (Diplomat Star). Earth. Wealth, responsibility, real estate. Diligence, stability.",
        "business": "Excellent for real estate, agriculture, construction, wealth accumulation. Patience and hard work.",
        "relationship": "Responsible, stable partnerships. Long-term commitment.",
        "health": "Steady health. Requires consistent care.",
        "recommendation": "Be patient and responsible. Focus on long-term wealth accumulation, real estate, or building a solid foundation."
    },
    "天英": {
        "general": "Heavenly Hero (Fearless Star). Fire. Brightness, fame, passion, beauty, but also fire/conflict.",
        "business": "Fame, recognition, but potential for burnout. Good for marketing, PR, entertainment.",
        "relationship": "Passionate, dramatic relationships. High visibility.",
        "health": "Inflammation or heat-related issues. Stress management.",
        "recommendation": "Seek fame and recognition. Promote your brand. Be careful of conflict and burnout."
    },

    # ========== 8 Deities (八神) ==========
    "值符": {
        "general": "Chief (Zhi Fu). Wood/Earth. The leader, protection, wealth, high status. The most auspicious deity.",
        "business": "Leadership, protection from loss, high-level assistance. Smooth sailing.",
        "relationship": "Noble partner, protection. High status.",
        "health": "Protection, recovery. Best for health.",
        "recommendation": "Take the lead with confidence. You are protected. Aim high and seek assistance from powerful people."
    },
    "螣蛇": {
        "general": "Snake (Teng She). Fire. Deception, hypocrisy, supernatural, changing. Unreliable.",
        "business": "Fraud, deception, changing market conditions. Be careful of contracts.",
        "relationship": "Deception, lies, changing feelings. Unreliable partner.",
        "health": "Nightmares, strange illnesses, mental health.",
        "recommendation": "Be extremely vigilant against deception and fraud. Adapt to changing circumstances. Do not trust appearances."
    },
    "太阴": {
        "general": "Moon (Tai Yin). Metal. Secrets, planning, darkness, female help. Hidden assistance.",
        "business": "Secret planning, strategy, hidden assets. Help from women.",
        "relationship": "Secret love, female partner, gentle emotions.",
        "health": "Hidden illnesses, female health issues.",
        "recommendation": "Plan in secret and keep your strategy hidden. Seek assistance from women or behind-the-scenes figures."
    },
    "六合": {
        "general": "Six Harmony (Liu He). Wood. Relationships, marriage, partnership, negotiation. Bringing things together.",
        "business": "Partnerships, deals, networking, negotiation. Bringing people together.",
        "relationship": "Marriage, union, harmony. Multiple partners.",
        "health": "Multiple illnesses or complications. Binding.",
        "recommendation": "Focus on networking, partnerships, and negotiation. Bring people together. Good for marriage and teamwork."
    },
    "白虎": {
        "general": "White Tiger (Bai Hu). Metal. Ferocity, injury, blood, pressure. Very inauspicious.",
        "business": "Conflict, pressure, injury, technical skills. High stress.",
        "relationship": "Conflict, abuse, pressure. Dangerous.",
        "health": "Injury, blood, surgery, severe illness.",
        "recommendation": "Prepare for high pressure and conflict. Use your technical skills to survive. Avoid confrontation if possible."
    },
    "玄武": {
        "general": "Black Tortoise (Xuan Wu). Water. Theft, deception, loss, secrets. Hidden danger.",
        "business": "Theft, loss of money, deception, hidden enemies. Fraud.",
        "relationship": "Cheating, lies, secret affairs. Betrayal.",
        "health": "Unclear illness, dizziness, kidney issues.",
        "recommendation": "Guard your assets and secrets closely. Watch out for theft, fraud, and betrayal. Do not trust easily."
    },
    "九地": {
        "general": "Nine Earth (Jiu Di). Earth. Stability, slowness, long-term, hiding. Passive.",
        "business": "Long-term investment, stability, agriculture. Slow growth.",
        "relationship": "Stable, boring, long-term. Passive.",
        "health": "Chronic illness, slow recovery. Depression.",
        "recommendation": "Adopt a low profile and focus on stability. Think long-term. Do not rush; patience is key."
    },
    "九天": {
        "general": "Nine Heavens (Jiu Tian). Metal. Active, fast, travel, high ambition. Dynamic.",
        "business": "Expansion, travel, high goals, international business. Fast moving.",
        "relationship": "Active, travel together, high expectations.",
        "health": "High blood pressure, dizziness. Active recovery.",
        "recommendation": "Aim high and move fast. Expand your horizons and travel. Be ambitious and dynamic."
    },

    # ========== 10 Heavenly Stems (天干) ==========
    "甲": {
        "general": "Yang Wood. Noble person, leadership, the best, number one. Tall trees.",
        "business": "Leadership tasks, managers, bosses. High quality.",
        "relationship": "Noble, high-quality partner. Leadership.",
        "health": "Head, liver. Strong constitution.",
        "recommendation": "Act as a leader. Strive for excellence and quality. Stand tall and confident."
    },
    "乙": {
        "general": "Yin Wood. Women, winding path, artistic. Flexibility.",
        "business": "Art, exquisite crafts, artistic work. Negotiation.",
        "relationship": "Wife, elegant women. Flexibility.",
        "health": "Liver, neck. Flexibility.",
        "recommendation": "Be flexible and adaptable. Use soft skills and negotiation. Pursue artistic or creative solutions."
    },
    "丙": {
        "general": "Yang Fire. Transformation, chaos, breakthrough. Passionate.",
        "business": "Disruptive change, innovation. Decisive action.",
        "relationship": "Passion, conflict, third party.",
        "health": "Small intestine, eyes. Inflammation.",
        "recommendation": "Create a breakthrough or transformation. Be decisive and passionate, but watch out for chaos."
    },
    "丁": {
        "general": "Yin Fire. Hope, documents, contracts, inspiration. Auspicious.",
        "business": "Contracts, agreements, intellectual property. Hope.",
        "relationship": "Mistress, delicate beauty. Romance.",
        "health": "Heart, blood. Gentle warmth.",
        "recommendation": "Focus on documents, contracts, and details. Look for the spark of inspiration or hope."
    },
    "戊": {
        "general": "Yang Earth. Capital, finance, assets. Wall or mountain.",
        "business": "Capital, investment, property. Trustworthiness.",
        "relationship": "Solid foundation, stability.",
        "health": "Stomach, nose. Strong foundation.",
        "recommendation": "Manage your capital and assets. Be reliable and trustworthy. Build a solid foundation."
    },
    "己": {
        "general": "Yin Earth. Desire, plan, scheme. Hidden resources.",
        "business": "Strategic planning, hidden assets. Ideas.",
        "relationship": "Hidden desires, planning.",
        "health": "Spleen, stomach. Internal issues.",
        "recommendation": "Plan strategically and keep your resources hidden. Use your creativity and ideas."
    },
    "庚": {
        "general": "Yang Metal. Enemy, competitor, lawsuit. Obstacles.",
        "business": "Competition, obstacles, challenges. Fighting.",
        "relationship": "Competition, obstacles. Rivals.",
        "health": "Large intestine, bones. Blockage.",
        "recommendation": "Prepare for a fight or competition. Overcome the obstacle with strength. Be tough."
    },
    "辛": {
        "general": "Yin Metal. Mistake, problem, crime. Refinement.",
        "business": "Mistakes, problems, legal issues. Correction.",
        "relationship": "Mistakes, regrets. Refinement.",
        "health": "Lungs, skin. Sensitivity.",
        "recommendation": "Correct your mistakes and refine your approach. Watch out for legal issues or errors."
    },
    "壬": {
        "general": "Yang Water. Journey, movement, change. Flow.",
        "business": "Travel, logistics, movement. Change.",
        "relationship": "Movement, travel. Instability.",
        "health": "Bladder, kidneys. Circulation.",
        "recommendation": "Go with the flow. Adapt to changes and keep moving. Consider travel or logistics."
    },
    "癸": {
        "general": "Yin Water. Network, relationship, communication. Hidden connections.",
        "business": "Networking, communication, hidden channels.",
        "relationship": "Emotional connection, secrets.",
        "health": "Kidneys, reproductive system.",
        "recommendation": "Leverage your network and connections. Communicate effectively but discreetly."
    },

    # ========== 12 Earthly Branches (地支) ==========
    "子": {
        "general": "Rat. Water. Wisdom, intelligence, resourcefulness.",
        "business": "Strategy, research, planning.",
        "relationship": "Smart, adaptable partner.",
        "health": "Kidneys, ears.",
        "recommendation": "Use your wisdom and resourcefulness. Plan strategically."
    },
    "丑": {
        "general": "Ox. Earth. Diligence, stability, perseverance.",
        "business": "Hard work, real estate, stability.",
        "relationship": "Reliable, stubborn partner.",
        "health": "Stomach, spleen.",
        "recommendation": "Work hard and persevere. Stay grounded and stable."
    },
    "寅": {
        "general": "Tiger. Wood. Courage, leadership, ambition.",
        "business": "Leadership, entrepreneurship, risk.",
        "relationship": "Dominant, ambitious partner.",
        "health": "Liver, gallbladder.",
        "recommendation": "Be courageous and ambitious. Take the lead."
    },
    "卯": {
        "general": "Rabbit. Wood. Kindness, diplomacy, creativity.",
        "business": "Design, negotiation, care.",
        "relationship": "Gentle, artistic partner.",
        "health": "Liver, fingers.",
        "recommendation": "Use diplomacy and creativity. Be gentle but persistent."
    },
    "辰": {
        "general": "Dragon. Earth. Power, authority, ambition.",
        "business": "Management, large projects, authority.",
        "relationship": "Powerful, egoistic partner.",
        "health": "Stomach, skin.",
        "recommendation": "Exercise your authority. Aim for major achievements."
    },
    "巳": {
        "general": "Snake. Fire. Wisdom, intuition, change.",
        "business": "Consulting, analysis, change.",
        "relationship": "Wise, changeable partner.",
        "health": "Heart, face.",
        "recommendation": "Trust your intuition. Adapt to changes wisely."
    },
    "午": {
        "general": "Horse. Fire. Passion, energy, visibility.",
        "business": "Marketing, sales, public speaking.",
        "relationship": "Passionate, fleeting partner.",
        "health": "Heart, eyes.",
        "recommendation": "Show your passion and energy. Be visible and active."
    },
    "未": {
        "general": "Goat. Earth. Patience, support, detail.",
        "business": "Service, hospitality, support.",
        "relationship": "Supportive, gentle partner.",
        "health": "Stomach, spine.",
        "recommendation": "Be patient and supportive. Pay attention to details."
    },
    "申": {
        "general": "Monkey. Metal. Agility, problem solving, travel.",
        "business": "Logistics, engineering, travel.",
        "relationship": "Fun, unstable partner.",
        "health": "Lungs, bones.",
        "recommendation": "Be agile and flexible. Solve problems creatively."
    },
    "酉": {
        "general": "Rooster. Metal. Precision, confidence, beauty.",
        "business": "Fashion, jewelry, accounting.",
        "relationship": "Attractive, critical partner.",
        "health": "Lungs, mouth.",
        "recommendation": "Be precise and confident. Focus on aesthetics and quality."
    },
    "戌": {
        "general": "Dog. Earth. Loyalty, honesty, protection.",
        "business": "Security, auditing, trust.",
        "relationship": "Loyal, defensive partner.",
        "health": "Stomach, legs.",
        "recommendation": "Be loyal and honest. Protect what is important."
    },
    "亥": {
        "general": "Pig. Water. Wealth, happiness, comfort.",
        "business": "Food, entertainment, wealth.",
        "relationship": "Happy, easy-going partner.",
        "health": "Kidneys, blood.",
        "recommendation": "Enjoy the process. Focus on wealth and comfort."
    }
}

@tool(parse_docstring=True)
def symbol_lookup(symbol_name: str, context: str = "general") -> str:
    """Look up the meaning and recommendation of a QMDJ symbol.

    Args:
        symbol_name: The Chinese name of the symbol (e.g., '天芮', '死門', '甲').
        context: The context of the reading ('general', 'business', 'relationship', 'health'). Defaults to 'general'.
    """
    data = SYMBOL_DATA.get(symbol_name)
    if not data:
        return f"Symbol '{symbol_name}' not found in database."
    
    meaning = data.get(context, data.get("general", "No description available."))
    recommendation = data.get("recommendation", "No specific recommendation available.")
    
    return f"""**Symbol:** {symbol_name}
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
    # Simplified logic for demonstration
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
    
    # Normalize input
    e1 = element1.capitalize()
    e2 = element2.capitalize()
    
    if e1 == e2:
        return f"Harmony (Same element: {e1})"
        
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
    
    if total == 0:
        return "No factors provided for scoring."
    
    favorable_pct = int((pos_count / total) * 100)
    unfavorable_pct = 100 - favorable_pct
    
    # Context-aware scoring logic
    all_positive = set(positive_factors)
    all_negative = set(negative_factors)
    
    # Absolute Auspicious Symbols (generally favorable across contexts)
    absolute_auspicious = {
        # Doors (3 best)
        "開門": "Open Door",
        "休門": "Rest Door",
        "生門": "Life Door",
        # Stars (2 best)
        "天心": "Doctor Star",
        "天輔": "Advisor Star",
        # Stems (4 best)
        "甲": "Jia",
        "乙": "Yi",
        "丙": "Bing",
        "丁": "Ding",
        # Deities (4 best)
        "值符": "Chief/Leader",
        "九天": "Nine Heavens",
        "九地": "Nine Earth",
        "六合": "Six Harmony",
    }
    
    # Absolute Inauspicious Symbols (generally unfavorable across contexts)
    absolute_inauspicious = {
        # Doors (3 worst)
        "傷門": "Injury Door",
        "杜門": "Delusion Door",
        "死門": "Death Door",
        # Stars (3 worst)
        "天蓬": "Bandit Star",
        "天芮": "Problem Star",
        "天冲": "Impulse Star",
        # Stems (2 worst)
        "庚": "Geng",
        "辛": "Xin",
        # Deities (4 worst)
        "螣蛇": "Serpent/Snake",
        "玄武": "Black Tortoise",
        "白虎": "White Tiger",
    }
    
    # Detect strong signals
    strong_positive_symbols = [name for symbol, name in absolute_auspicious.items() 
                               if symbol in all_positive]
    strong_negative_symbols = [name for symbol, name in absolute_inauspicious.items() 
                               if symbol in all_negative]
    
    has_strong_positive = len(strong_positive_symbols) > 0
    has_strong_negative = len(strong_negative_symbols) > 0
    
    # Determine confidence based on signal clarity and presence of absolute symbols
    if has_strong_positive and not has_strong_negative and favorable_pct > 60:
        confidence = "High - Strong auspicious symbols present"
        confidence_detail = f"Detected: {', '.join(strong_positive_symbols)}"
    elif has_strong_negative and not has_strong_positive and unfavorable_pct > 60:
        confidence = "High - Strong inauspicious symbols present"
        confidence_detail = f"Detected: {', '.join(strong_negative_symbols)}"
    elif has_strong_positive and has_strong_negative:
        confidence = "Moderate - Mixed signals (both auspicious and inauspicious symbols)"
        confidence_detail = f"Positive: {', '.join(strong_positive_symbols)} | Negative: {', '.join(strong_negative_symbols)}"
    elif abs(favorable_pct - 50) > 30:
        confidence = "Moderate-High - Clear directional signal"
        confidence_detail = "Based on factor count distribution"
    elif abs(favorable_pct - 50) > 15:
        confidence = "Moderate - Slight directional lean"
        confidence_detail = "Based on factor count distribution"
    else:
        confidence = "Low - Conflicting signals, unclear direction"
        confidence_detail = "Nearly equal positive and negative factors"
    
    # Determine strength of the reading
    if abs(favorable_pct - 50) < 15:
        strength = "Weak/Unclear"
    elif abs(favorable_pct - 50) < 30:
        strength = "Moderate"
    else:
        strength = "Strong"
    
    # Build detailed output
    result = f"""**Probability Assessment:**
- Favorable: {favorable_pct}%
- Unfavorable: {unfavorable_pct}%
- Strength: {strength}
- Confidence: {confidence}

**Signal Analysis:**
- {confidence_detail}
- Positive factors analyzed: {pos_count}
- Negative factors analyzed: {neg_count}
"""
    
    # Add notes if there are strong symbols
    if strong_positive_symbols or strong_negative_symbols:
        result += f"\n**Key Symbols Detected:**\n"
        if strong_positive_symbols:
            result += f"- Auspicious: {', '.join(strong_positive_symbols)}\n"
        if strong_negative_symbols:
            result += f"- Inauspicious: {', '.join(strong_negative_symbols)}\n"
    
    return result

@tool(parse_docstring=True)
def reflect_on_reading(reflection: str) -> str:
    """Tool for strategic reflection and reasoning during analysis.

    Use this to pause and think through interpretations, conflicts, and decisions.

    Args:
        reflection: Your detailed reflection on the analysis
    """
    return f"💭 Reflection recorded: {reflection}"
