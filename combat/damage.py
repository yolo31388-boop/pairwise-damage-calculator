"""伤害计算战斗公式系统"""
from dataclasses import dataclass
import random


@dataclass
class CombatStats:
    attack: float = 10.0
    defense: float = 5.0
    crit_rate: float = 0.1
    crit_damage: float = 1.5
    crit_resistance: float = 0.0
    dodge_rate: float = 0.05
    hit_rate: float = 0.95
    level: int = 1
    element: str = "physical"  # physical, fire, water, earth, wind
    damage_type: str = "physical"  # physical, magic, true, chaos
    shield: float = 0.0
    reflect_rate: float = 0.0


@dataclass
class DamageResult:
    damage: float
    is_crit: bool = False
    is_dodge: bool = False
    damage_type: str = "physical"
    element: str = "physical"
    absorbed: float = 0.0
    reflected: float = 0.0


class DamageCalculator:
    MAX_CRIT_RATE = 0.8
    MAX_DODGE_RATE = 0.8
    LEVEL_FACTOR = 0.02
    MIN_LEVEL_MULTIPLIER = 0.5
    MAX_LEVEL_MULTIPLIER = 2.0

    TYPE_COLORS = {
        "physical": "orange",
        "magic": "blue",
        "true": "white",
        "chaos": "purple",
    }

    def __init__(self):
        self.element_advantage = {
            ("fire", "wind"): 1.5,
            ("water", "fire"): 1.5,
            ("earth", "water"): 1.5,
            ("wind", "earth"): 1.5,
        }

    def calculate_damage(self, attacker: CombatStats, defender: CombatStats) -> DamageResult:
        """计算伤害：攻击力 - 防御力，并考虑属性克制、等级差、暴击与伤害类型"""
        element_mult = self.calculate_element_multiplier(attacker.element, defender.element)
        level_mult = self.calculate_level_difference(attacker.level, defender.level)

        # 必暴（暴击率叠满）时直接按暴击结算，否则由战斗循环调用 calculate_crit 判定
        is_crit = attacker.crit_rate >= 1.0
        crit_mult = attacker.crit_damage if is_crit else 1.0

        raw = attacker.attack * element_mult * level_mult * crit_mult
        damage, absorbed = self.apply_damage_type(raw, attacker.damage_type, defender)
        reflected = self.calculate_reflect(damage, defender)

        return DamageResult(
            damage=damage,
            is_crit=is_crit,
            damage_type=attacker.damage_type,
            element=attacker.element,
            absorbed=absorbed,
            reflected=reflected,
        )

    def calculate_crit(self, attacker: CombatStats, defender: CombatStats) -> tuple[bool, float]:
        """计算暴击：看暴击率、暴击伤害，受暴击上限和防御方暴击抗性约束"""
        effective_rate = attacker.crit_rate - defender.crit_resistance
        effective_rate = max(0.0, min(self.MAX_CRIT_RATE, effective_rate))
        is_crit = random.random() < effective_rate
        crit_multiplier = attacker.crit_damage if is_crit else 1.0
        return is_crit, crit_multiplier

    def calculate_dodge(self, attacker: CombatStats, defender: CombatStats) -> bool:
        """计算闪避：闪避率受攻击方命中、闪避上限和等级压制影响"""
        dodge_rate = min(defender.dodge_rate, self.MAX_DODGE_RATE)
        # 命中对抗闪避：命中越低越容易被闪避
        effective = dodge_rate - (attacker.hit_rate - 1.0)
        # 等级压制：低级打高级有命中惩罚
        if attacker.level < defender.level:
            effective += (defender.level - attacker.level) * 0.01
        effective = max(0.0, min(self.MAX_DODGE_RATE, effective))
        return random.random() < effective

    def apply_damage_type(self, damage: float, damage_type: str, defender: CombatStats) -> tuple[float, float]:
        """应用伤害类型（物理/魔法/实数/混沌），并结算护盾吸收。

        返回 (实际伤害, 护盾吸收量)。
        """
        if damage_type == "physical":
            result = max(0.0, damage - defender.defense)
        elif damage_type == "magic":
            result = damage * 0.9  # 魔抗减免
        elif damage_type == "true":
            result = damage  # 实数伤害无视防御
        elif damage_type == "chaos":
            # 混沌伤害：25% 加成，但只无视一半防御
            result = max(0.0, damage * 1.25 - defender.defense * 0.5)
        else:
            result = damage

        absorbed = min(defender.shield, result)
        return result - absorbed, absorbed

    def calculate_reflect(self, damage: float, defender: CombatStats) -> float:
        """计算反伤甲反弹的伤害"""
        return damage * defender.reflect_rate

    def calculate_element_multiplier(self, attacker_element: str, defender_element: str) -> float:
        """计算属性克制倍率"""
        return self.element_advantage.get((attacker_element, defender_element), 1.0)

    def calculate_level_difference(self, attacker_level: int, defender_level: int) -> float:
        """计算等级差倍率：每差一级伤害浮动 2%，限制在 [0.5, 2.0]"""
        diff = attacker_level - defender_level
        multiplier = 1.0 + diff * self.LEVEL_FACTOR
        return max(self.MIN_LEVEL_MULTIPLIER, min(self.MAX_LEVEL_MULTIPLIER, multiplier))

    def format_damage(self, result: DamageResult) -> dict:
        """格式化伤害显示：按伤害类型分类颜色，暴击有特效，伤害数字上浮"""
        color = self.TYPE_COLORS.get(result.damage_type, "gray")
        return {
            "damage": int(result.damage),
            "is_crit": result.is_crit,
            "color": color,
            "crit_effect": result.is_crit,
            "scale": 1.5 if result.is_crit else 1.0,
            "float": True,
            "float_distance": 60 if result.is_crit else 40,
        }
