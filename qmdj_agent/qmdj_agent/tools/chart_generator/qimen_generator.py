"""
QMDJ Chart Generator - Authentic Implementation

This module generates Qi Men Dun Jia (奇门遁甲) charts using:
1. lunar-python: For accurate astronomical data (Solar Terms, GanZhi) - supports unlimited timeframe.
2. Ported Logic: Algorithms adapted from 'kinqimen' package (Chai Bu method).

Features:
- Accurate Four Pillars (Year, Month, Day, Hour)
- Precise Solar Term calculation
- Authentic QMDJ algorithms (Ju number, plate rotation)
- Complete chart metadata (9 Palaces, Stems, Doors, Stars, Deities)
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional
from lunar_python import Solar, Lunar, JieQi

class QimenGenerator:
    """QMDJ Chart Generator using lunar-python and Chai Bu method."""
    
    # --- Constants ---
    TIAN_GAN = list("甲乙丙丁戊己庚辛壬癸")
    DI_ZHI = list("子丑寅卯辰巳午未申酉戌亥")
    EIGHT_GUA = list("坎坤震巽中乾兑艮离")
    # Standard QMDJ Palace Order (1-9)
    # 1:Kan, 2:Kun, 3:Zhen, 4:Xun, 5:Center, 6:Qian, 7:Dui, 8:Gen, 9:Li
    PALACE_NAMES = ["", "坎", "坤", "震", "巽", "中", "乾", "兑", "艮", "离"]
    
    DOORS = list("休生伤杜景死惊开")
    STARS = list("蓬任冲辅英禽柱心") # Note: Qin (禽) is usually in center/with Rui
    DEITIES = ["值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"] # Yang Dun order
    DEITIES_YIN = ["值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"] # Yin Dun order (White Tiger instead of Tiger)
    
    # Magic Square Numbers for Palaces
    # 4 9 2
    # 3 5 7
    # 8 1 6
    GUA_TO_NUM = {"坎": 1, "坤": 2, "震": 3, "巽": 4, "中": 5, "乾": 6, "兑": 7, "艮": 8, "离": 9}
    NUM_TO_GUA = {v: k for k, v in GUA_TO_NUM.items()}
    
    # Clockwise rotation path for 8 palaces (skipping center)
    # 坎1 -> 艮8 -> 震3 -> 巽4 -> 離9 -> 坤2 -> 兌7 -> 乾6 -> 坎1
    ROTATION_PATH = [1, 8, 3, 4, 9, 2, 7, 6]
    
    def __init__(self, year: int, month: int, day: int, hour: int):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.dt = datetime(year, month, day, hour)
        
        # Initialize Lunar/Solar objects
        # lunar-python Solar.fromYmdHms takes local time.
        # We don't need to adjust for timezone here for the Solar object itself 
        # as it represents the "Civil Time" we are interested in.
        # However, for accurate JieQi (Solar Term) which is astronomical, 
        # lunar-python handles it internally but we should be aware.
        self.solar = Solar.fromYmdHms(year, month, day, hour, 0, 0)
        self.lunar = self.solar.getLunar()
        
        # Chart Data Containers
        self.gan_zhi = [] # [Y, M, D, H]
        self.jie_qi = ""
        self.yuan = "" # Upper/Middle/Lower
        self.yin_yang = "" # 阴/阳
        self.chart = {} # Palace data
        
        self.horse_star = "" # 驛馬
        self.empty_death = "" # 空亡

    def generate(self) -> Dict:
        """Generate the complete QMDJ chart."""
        # 1. Calculate Four Pillars & Solar Term
        self._calc_base_info()
        
        # 2. Calculate Horse Star & Empty Death
        self._calc_horse_star()
        self._calc_empty_death()
        
        # 3. Determine Ju (局) - Chai Bu Method
        self._calc_ju()
        
        # 4. Generate Plates
        self._generate_plates()
        
        return self._format_output()

    def _calc_horse_star(self):
        """Calculate Horse Star (Yi Ma) based on Hour Branch."""
        # Shen-Zi-Chen -> Yin
        # Yin-Wu-Xu -> Shen
        # Si-You-Chou -> Hai
        # Hai-Mao-Wei -> Si
        h_zhi = self.gan_zhi[3][1]
        
        if h_zhi in "申子辰":
            self.horse_star = "寅"
        elif h_zhi in "寅午戌":
            self.horse_star = "申"
        elif h_zhi in "巳酉丑":
            self.horse_star = "亥"
        elif h_zhi in "亥卯未":
            self.horse_star = "巳"
            
    def _calc_empty_death(self):
        """Calculate Empty/Death (Kong Wang) based on Xun Shou."""
        # The Xun Shou (e.g. Jia Zi) determines the empty branches.
        # We can find the Xun from the Hour GanZhi.
        h_gan = self.gan_zhi[3][0]
        h_zhi = self.gan_zhi[3][1]
        
        # Find distance from Jia
        gan_idx = self.TIAN_GAN.index(h_gan)
        zhi_idx = self.DI_ZHI.index(h_zhi)
        
        # Xun Shou Branch index = (Zhi - Gan) % 12
        xun_zhi_idx = (zhi_idx - gan_idx) % 12
        xun_zhi = self.DI_ZHI[xun_zhi_idx] # Zi, Xu, Shen, Wu, Chen, Yin
        
        # Map Xun to Empty Branches
        # Jia Zi (Zi) -> Xu Hai
        # Jia Xu (Xu) -> Shen You
        # Jia Shen (Shen) -> Wu Wei
        # Jia Wu (Wu) -> Chen Si
        # Jia Chen (Chen) -> Yin Mao
        # Jia Yin (Yin) -> Zi Chou
        
        EMPTY_MAP = {
            "子": "戌亥", "戌": "申酉", "申": "午未",
            "午": "辰巳", "辰": "寅卯", "寅": "子丑"
        }
        self.empty_death = EMPTY_MAP.get(xun_zhi, "")

    def _calc_base_info(self):
        """Calculate GanZhi and Solar Term."""
        # Four Pillars
        y_gz = self.lunar.getYearInGanZhi()
        m_gz = self.lunar.getMonthInGanZhi()
        d_gz = self.lunar.getDayInGanZhi()
        h_gz = self.lunar.getTimeInGanZhi()
        self.gan_zhi = [y_gz, m_gz, d_gz, h_gz]
        
        # Solar Term (Jie Qi)
        prev_jq = self.lunar.getPrevJieQi(True) # True = include today
        self.jie_qi = prev_jq.getName()
        
        # Calculate Yuan (Upper/Middle/Lower)
        # Simplified Yuan Calculation (Chai Bu):
        d_gz = self.lunar.getDayInGanZhi()
        day_gan_idx = self.TIAN_GAN.index(d_gz[0])
        day_zhi_idx = self.DI_ZHI.index(d_gz[1])
        
        if day_gan_idx < 5:
            diff = day_gan_idx 
            futou_gan = "甲"
        else:
            diff = day_gan_idx - 5
            futou_gan = "己"
            
        futou_zhi_idx = (day_zhi_idx - diff) % 12
        futou_zhi = self.DI_ZHI[futou_zhi_idx]
        self.futou = f"{futou_gan}{futou_zhi}"
        
        if futou_zhi in "子午卯酉":
            self.yuan = "上元"
            self.yuan_idx = 1
        elif futou_zhi in "寅申巳亥":
            self.yuan = "中元"
            self.yuan_idx = 2
        else:
            self.yuan = "下元"
            self.yuan_idx = 3

    def _calc_ju(self):
        """Calculate Yin/Yang Dun and Ju Number."""
        # 1. Yin/Yang Dun
        YANG_DUN_JQ = ["冬至", "小寒", "大寒", "立春", "雨水", "驚蟄", 
                       "春分", "清明", "穀雨", "立夏", "小滿", "芒種"]
        
        if self.jie_qi in YANG_DUN_JQ:
            self.yin_yang = "阳"
        else:
            self.yin_yang = "阴"
            
        # 2. Ju Number (局數)
        JU_MAP = {
            "冬至": [1, 7, 4], "小寒": [2, 8, 5], "大寒": [3, 9, 6],
            "立春": [8, 5, 2], "雨水": [9, 6, 3], "惊蛰": [1, 7, 4],
            "春分": [3, 9, 6], "清明": [4, 1, 7], "谷雨": [5, 2, 8],
            "立夏": [4, 1, 7], "小满": [5, 2, 8], "芒种": [6, 3, 9],
            "夏至": [9, 3, 6], "小暑": [8, 2, 5], "大暑": [7, 1, 4],
            "立秋": [2, 5, 8], "处暑": [1, 4, 7], "白露": [9, 3, 6],
            "秋分": [7, 1, 4], "寒露": [6, 9, 3], "霜降": [5, 8, 2],
            "立冬": [6, 9, 3], "小雪": [5, 8, 2], "大雪": [4, 7, 1]
        }
        
        if self.jie_qi in JU_MAP:
            self.ju_num = JU_MAP[self.jie_qi][self.yuan_idx - 1]
        else:
            self.ju_num = 1 

    def _generate_plates(self):
        """Generate the 4 Plates (Earth, Heaven, Man, Deity)."""
        
        # 1. Earth Plate (Di Pan)
        pai_gan = list("戊己庚辛壬癸丁丙乙")
        earth_plate = {} 
        
        curr_pos = self.ju_num
        for stem in pai_gan:
            earth_plate[curr_pos] = stem
            if self.yin_yang == "阳":
                curr_pos += 1
                if curr_pos > 9: curr_pos = 1
            else:
                curr_pos -= 1
                if curr_pos < 1: curr_pos = 9
                
        self.earth_plate = earth_plate
        
        # 2. Find Xun Shou (旬首) & Zhi Fu / Zhi Shi
        h_gan = self.gan_zhi[3][0]
        h_zhi = self.gan_zhi[3][1]
        
        h_gan_idx = self.TIAN_GAN.index(h_gan)
        h_zhi_idx = self.DI_ZHI.index(h_zhi)
        
        diff = (h_zhi_idx - h_gan_idx) % 12
        xun_shou_zhi = self.DI_ZHI[diff] 
        
        XUN_MAP = {
            "子": "戊", "戌": "己", "申": "庚", 
            "午": "辛", "辰": "壬", "寅": "癸"
        }
        self.xun_shou = f"甲{xun_shou_zhi}{XUN_MAP[xun_shou_zhi]}"
        lead_stem = XUN_MAP[xun_shou_zhi] 
        
        lead_loc = 0
        for loc, stem in earth_plate.items():
            if stem == lead_stem:
                lead_loc = loc
                break
                
        STAR_MAP = {1:"天蓬", 2:"天芮", 3:"天冲", 4:"天辅", 5:"天禽", 6:"天心", 7:"天柱", 8:"天任", 9:"天英"}
        DOOR_MAP = {1:"休门", 2:"死门", 3:"伤门", 4:"杜门", 5:"", 6:"开门", 7:"惊门", 8:"生门", 9:"景门"}
        
        self.zhi_fu_star = STAR_MAP[lead_loc]
        if lead_loc == 5: self.zhi_fu_star = "天禽" 
        
        self.zhi_shi_door = DOOR_MAP[lead_loc]
        if lead_loc == 5: self.zhi_shi_door = "死门" 
        
        # 3. Heaven Plate (Tian Pan)
        target_stem = h_gan
        if target_stem == "甲": target_stem = lead_stem
        
        target_loc = 0
        for loc, stem in earth_plate.items():
            if stem == target_stem:
                target_loc = loc
                break
        
        STD_STAR_RING = ["天蓬", "天任", "天冲", "天辅", "天英", "天芮", "天柱", "天心"]
        
        zf_name = self.zhi_fu_star
        if zf_name == "天禽": zf_name = "天芮"
        
        try:
            start_idx = STD_STAR_RING.index(zf_name)
        except ValueError:
            start_idx = 5 
            
        try:
            target_rot_idx = self.ROTATION_PATH.index(target_loc)
        except ValueError:
            target_rot_idx = 0 
            if target_loc == 5: target_rot_idx = self.ROTATION_PATH.index(2) 
            
        heaven_plate = {} 
        heaven_stem_plate = {} 
        
        for i in range(8):
            star = STD_STAR_RING[(start_idx + i) % 8]
            pal_num = self.ROTATION_PATH[(target_rot_idx + i) % 8]
            heaven_plate[pal_num] = star
            
            orig_home = 0
            for k, v in STAR_MAP.items():
                if v == star: 
                    orig_home = k
                    break
            if star == "天芮": orig_home = 2 
            
            stem_val = earth_plate.get(orig_home, "")
            heaven_stem_plate[pal_num] = stem_val
            
            if star == "天芮":
                center_stem = earth_plate.get(5, "")
                heaven_stem_plate[pal_num] = f"{stem_val}{center_stem}"
                
        heaven_plate[5] = "" 
        
        # 4. Man Plate (Ren Pan - Doors)
        xs_zhi_idx = self.DI_ZHI.index(xun_shou_zhi)
        curr_h_idx = self.DI_ZHI.index(h_zhi)
        
        diff_hours = (curr_h_idx - xs_zhi_idx) % 12
        
        # Move Zhi Shi
        # Zhi Shi moves along the NUMERICAL sequence (1-9), not the spatial ring.
        # Yang Dun: 1->2->3...
        # Yin Dun: 9->8->7...
        
        if self.yin_yang == "阳":
            dest_door_loc = (lead_loc + diff_hours)
            while dest_door_loc > 9:
                dest_door_loc -= 9
            if dest_door_loc == 0: dest_door_loc = 9 
        else:
            dest_door_loc = (lead_loc - diff_hours)
            while dest_door_loc < 1:
                dest_door_loc += 9
                
        # Now arrange 8 doors starting from dest_door_loc
        # The doors themselves are arranged in the standard ring order (Clockwise)
        # into the Palaces (Clockwise spatial path).
        # We need to find where dest_door_loc is in the ROTATION_PATH to start filling.
        
        try:
            final_door_rot_idx = self.ROTATION_PATH.index(dest_door_loc)
        except ValueError:
            # If dest_door_loc is 5 (Center), it usually lodges in 2 (Kun)
            final_door_rot_idx = self.ROTATION_PATH.index(2)
        
        STD_DOOR_RING = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]
        
        zs_name = self.zhi_shi_door
        try:
            start_door_idx = STD_DOOR_RING.index(zs_name)
        except ValueError:
            start_door_idx = 0 
            
        man_plate = {}
        for i in range(8):
            door = STD_DOOR_RING[(start_door_idx + i) % 8]
            pal_num = self.ROTATION_PATH[(final_door_rot_idx + i) % 8]
            man_plate[pal_num] = door
            
        man_plate[5] = "" 
        
        # 5. Deity Plate (Shen Pan)
        curr_deity_ring = self.DEITIES # Simplified: Both Yang and Yin use same 2-char names now
        
        try:
            deity_rot_idx = self.ROTATION_PATH.index(target_loc)
        except ValueError:
            deity_rot_idx = 0
            
        deity_plate = {}
        for i in range(8):
            deity = curr_deity_ring[i]
            if self.yin_yang == "阳":
                pal_num = self.ROTATION_PATH[(deity_rot_idx + i) % 8]
            else:
                pal_num = self.ROTATION_PATH[(deity_rot_idx - i) % 8]
            deity_plate[pal_num] = deity
            
        deity_plate[5] = ""
        
        self.heaven_plate = heaven_plate
        self.heaven_stem_plate = heaven_stem_plate
        self.man_plate = man_plate
        self.deity_plate = deity_plate
        
    # Branch to Palace Mapping
    BRANCH_TO_PALACE = {
        "子": 1, "丑": 8, "寅": 8, "卯": 3, "辰": 4, "巳": 4,
        "午": 9, "未": 2, "申": 2, "酉": 7, "戌": 6, "亥": 6
    }

    def _format_output(self) -> Dict:
        """Format the chart data into a dictionary."""
        palaces_data = {}
        
        # Identify special palaces
        horse_palace = self.BRANCH_TO_PALACE.get(self.horse_star)
        empty_branches = list(self.empty_death) # e.g. "申酉" -> ['申', '酉']
        empty_palaces = [self.BRANCH_TO_PALACE.get(b) for b in empty_branches]
        
        # Identify where Center (5) lodges
        center_stem = self.earth_plate.get(5, "")
        lodged_palace = 0
        for i in range(1, 10):
            if i == 5: continue
            h_stem = self.heaven_stem_plate.get(i, "")
            if center_stem in h_stem:
                lodged_palace = i
                break
        
        for i in range(1, 10):
            markers = []
            if i == horse_palace:
                markers.append("馬")
            if i in empty_palaces:
                markers.append("空")
            
            if i == 5 and lodged_palace:
                # Palace 5 inherits from lodged palace
                lodged_data = palaces_data.get(lodged_palace, {})
                # Note: We use the data already populated for the lodged palace
                # but we need to ensure the lodged palace is processed BEFORE palace 5
                # or we just fetch from the plates directly.
                # Since the loop is 1-9, and lodged_palace is usually 2 or 8 or something,
                # it might or might not be processed.
                # Let's just fetch from plates to be safe.
                p_h_stem = self.heaven_stem_plate.get(lodged_palace, "")
                p_star = self.heaven_plate.get(lodged_palace, "")
                p_door = self.man_plate.get(lodged_palace, "")
                p_deity = self.deity_plate.get(lodged_palace, "")
                
                # Inherit markers from lodged palace as well? 
                # User said "all the other keys should be same"
                p_markers = []
                if lodged_palace == horse_palace: p_markers.append("馬")
                if lodged_palace in empty_palaces: p_markers.append("空")

                palaces_data[i] = {
                    "palace_name": self.PALACE_NAMES[i],
                    "earth_stem": self.earth_plate.get(i, ""),
                    "heaven_stem": p_h_stem,
                    "star": p_star,
                    "door": p_door,
                    "deity": p_deity,
                    "markers": p_markers,
                    "all_symbols": [
                        p_h_stem, 
                        p_door,         
                        p_deity,       
                        p_star,      
                        self.earth_plate.get(i, "")        
                    ]
                }
            else:
                palaces_data[i] = {
                    "palace_name": self.PALACE_NAMES[i],
                    "earth_stem": self.earth_plate.get(i, ""),
                    "heaven_stem": self.heaven_stem_plate.get(i, ""),
                    "star": self.heaven_plate.get(i, ""),
                    "door": self.man_plate.get(i, ""),
                    "deity": self.deity_plate.get(i, ""),
                    "markers": markers,
                    "all_symbols": [
                        self.heaven_stem_plate.get(i, ""), 
                        self.man_plate.get(i, ""),         
                        self.deity_plate.get(i, ""),       
                        self.heaven_plate.get(i, ""),      
                        self.earth_plate.get(i, "")        
                    ]
                }
            
        return {
            "solar_date": self.dt.strftime("%Y-%m-%d %H:%M"),
            "timezone": "GMT+8",
            "gan_zhi": {
                "year": self.gan_zhi[0],
                "month": self.gan_zhi[1],
                "day": self.gan_zhi[2],
                "hour": self.gan_zhi[3]
            },
            "solar_term": self.jie_qi,
            "yuan": self.yuan,
            "yin_yang": self.yin_yang,
            "ju_num": self.ju_num,
            "formation": f"{self.yin_yang}遁{self.ju_num}局",
            "xun_shou": self.xun_shou,
            "zhi_fu": self.zhi_fu_star,
            "zhi_shi": self.zhi_shi_door,
            "horse_star": self.horse_star,
            "empty_death": self.empty_death,
            "palaces": palaces_data
        }

    def to_string(self, energy_data: Optional[Dict] = None) -> str:
        """String representation."""
        d = self.generate()
        lines = []
        lines.append(f"Time: {d['solar_date']} (GMT+8)")
        lines.append(f"GanZhi: {d['gan_zhi']['year']} {d['gan_zhi']['month']} {d['gan_zhi']['day']} {d['gan_zhi']['hour']}")
        lines.append(f"JieQi: {d['solar_term']} ({d['yuan']})")
        lines.append(f"Chart: {d['formation']}")
        lines.append(f"Xun Shou: {d['xun_shou']}")
        lines.append(f"Zhi Fu: {d['zhi_fu']} | Zhi Shi: {d['zhi_shi']}")
        lines.append(f"Horse: {d['horse_star']} | Empty: {d['empty_death']}")
        lines.append("-" * 40)
        
        grid_rows = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
        
        for row in grid_rows:
            row_str = []
            for p_idx in row:
                p = d['palaces'][p_idx]
                marker_str = "".join(p['markers'])
                if marker_str:
                    marker_str = f"[{marker_str}]"
                
                # Energy info
                energy_str = ""
                if energy_data and str(p_idx) in energy_data:
                    e = energy_data[str(p_idx)]
                    energy_val = e.get("energy", 100)
                    modifier = e.get("modifier", "normal")
                    
                    # Shorten modifiers for display
                    mod_abbr = []
                    if "tai_sui" in modifier: mod_abbr.append("TS")
                    if "death_emptiness" in modifier: mod_abbr.append("DE")
                    if "overflow" in modifier: mod_abbr.append("OF")
                    
                    mod_str = ",".join(mod_abbr)
                    energy_str = f"[{energy_val}% {mod_str}]" if mod_str else f"[{energy_val}%]"
                
                h_stem = p['heaven_stem']
                e_stem = p['earth_stem']
                
                if p_idx == 5:
                    # For Palace 5: Keep heaven_stem(earth_stem) with duplicate removal
                    if e_stem and e_stem in h_stem:
                        h_stem = h_stem.replace(e_stem, "", 1)
                    stem_str = f"{h_stem}({e_stem})" if e_stem else h_stem
                else:
                    # For all other palaces: Use (heaven_stem)earth_stem
                    stem_str = f"({h_stem}){e_stem}" if h_stem else e_stem
                
                s = f"{energy_str}{marker_str}{p['deity']}{p['star']}{p['door']}{stem_str}"
                row_str.append(f"{s:^26}") # Increased width for energy info
            lines.append("|".join(row_str))
            lines.append("-" * 82) # Increased separator width
            
        return "\n".join(lines)

if __name__ == "__main__":
    # Test
    q = QimenGenerator(2025, 12, 21, 20)
    print(q.to_string())
