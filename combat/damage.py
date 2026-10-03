"""伤害计算战斗公式系统"""
from dataclasses import dataclass
import random


# 基础命中率：闪避判定围绕它做攻防命中差计算
BASE_HIT_CHANCE = 0.9
# 闪避率上限，防止必闪
MAX_DODGE_CHANCE = 0.95
# 暴击率上限（100%），防止溢出
MAX_CRIT_CHANCE = 1.0
# 等级差每级对伤害的影响系数，倍率钳制在 [0.5, 1.5]
LEVEL_DAMAGE_FACTOR = 0.01
# 低级打高级时每级命中率惩罚
LEVEL_HIT_PENALTY = 0.01


@dataclass
class CombatStats:
    attack: float = 10.0
    defense: float = 5.0
    crit_rate: float = 0.1
    crit_damage: float = 1.5
    dodge_rate: float = 0.05
    hit_rate: float = 0.95
    level: int = 1
    element: str = "physical"  # physical, fire, water, earth, wind
    damage_type: str = "physical"  # physical, magic, true, chaos
    crit_resist: float = 0.0  # 暴击抗性，削减攻击方暴击率
    shield: float = 0.0  # 护盾值，优先吸收伤害
    reflect_rate: float = 0.0  # 反伤比例，反弹受到的伤害


@dataclass
class DamageResult:
    damage: float
    is_crit: bool = False
    is_dodge: bool = False
    damage_type: str = "physical"
    element: str = "physical"
    absorbed: float = 0.0  # 被护盾吸收的伤害
    reflected: float = 0.0  # 反弹给攻击方的伤害


class DamageCalculator:
    def __init__(self):
        self.element_advantage = {
            ("fire", "wind"): 1.5,
            ("water", "fire"): 1.5,
            ("earth", "water"): 1.5,
            ("wind", "earth"): 1.5,
        }
        self.type_colors = {
            "physical": "white",
            "magic": "blue",
            "true": "gold",
            "chaos": "purple",
        }

    def calculate_damage(self, attacker: CombatStats, defender: CombatStats) -> DamageResult:
        """计算伤害：防御减免 + 属性克制 + 等级差 + 暴击 + 闪避 + 伤害类型 + 护盾/反弹"""
        result = DamageResult(
            damage=0.0,
            damage_type=attacker.damage_type,
            element=attacker.element,
        )

        # 闪避判定：命中差 + 闪避上限 + 等级压制
        if self.calculate_dodge(attacker, defender):
            result.is_dodge = True
            return result

        # 基础伤害看防御
        damage = self.apply_damage_type(attacker.attack, attacker.damage_type, defender)

        # 属性克制
        damage *= self.calculate_element_multiplier(attacker.element, defender.element)

        # 等级差
        damage *= self.calculate_level_difference(attacker.level, defender.level)

        # 暴击：看暴击伤害、有上限、受暴击抗性影响（实数伤害不暴击）
        if attacker.damage_type != "true":
            is_crit, crit_multiplier = self.calculate_crit(attacker, defender)
            result.is_crit = is_crit
            damage *= crit_multiplier

        # 护盾吸收
        damage, result.absorbed = self.apply_shield(damage, defender)

        # 反伤甲反弹
        result.reflected = self.apply_reflect(damage, defender)

        result.damage = max(0.0, damage)
        return result

    def calculate_crit(self, attacker: CombatStats, defender: CombatStats) -> tuple[bool, float]:
        """计算暴击：暴击率受暴击抗性削减并钳制在上限内，暴击使用暴击伤害倍率"""
        effective_rate = attacker.crit_rate - defender.crit_resist
        effective_rate = max(0.0, min(MAX_CRIT_CHANCE, effective_rate))
        is_crit = random.random() < effective_rate
        crit_multiplier = attacker.crit_damage if is_crit else 1.0
        return is_crit, crit_multiplier

    def calculate_dodge(self, attacker: CombatStats, defender: CombatStats) -> bool:
        """计算闪避：命中与闪避对抗，闪避率有上限，低级打高级有命中惩罚"""
        dodge_chance = defender.dodge_rate + (BASE_HIT_CHANCE - attacker.hit_rate)
        # 等级压制：攻击方等级低于防御方时承受命中惩罚
        if attacker.level < defender.level:
            dodge_chance += (defender.level - attacker.level) * LEVEL_HIT_PENALTY
        dodge_chance = max(0.0, min(MAX_DODGE_CHANCE, dodge_chance))
        return random.random() < dodge_chance

    def apply_damage_type(self, damage: float, damage_type: str, defender: CombatStats) -> float:
        """应用伤害类型：物理吃防御、魔法吃魔抗、实数无视防御、混沌部分穿透"""
        if damage_type == "physical":
            return max(0.0, damage - defender.defense)
        elif damage_type == "magic":
            return damage * 0.9  # 简单魔抗
        elif damage_type == "true":
            return damage  # 实数伤害无视防御
        elif damage_type == "chaos":
            return max(0.0, damage - defender.defense * 0.5)  # 混沌伤害无视一半防御
        return damage

    def apply_shield(self, damage: float, defender: CombatStats) -> tuple[float, float]:
        """护盾吸收：护盾优先承受伤害，返回(剩余伤害, 吸收量)"""
        absorbed = min(damage, max(0.0, defender.shield))
        return damage - absorbed, absorbed

    def apply_reflect(self, damage: float, defender: CombatStats) -> float:
        """反伤甲：按反伤比例反弹实际受到的伤害"""
        return damage * max(0.0, defender.reflect_rate)

    def calculate_element_multiplier(self, attacker_element: str, defender_element: str) -> float:
        """计算属性克制倍率"""
        return self.element_advantage.get((attacker_element, defender_element), 1.0)

    def calculate_level_difference(self, attacker_level: int, defender_level: int) -> float:
        """计算等级差倍率：每级±1%，钳制在 [0.5, 1.5]"""
        multiplier = 1.0 + (attacker_level - defender_level) * LEVEL_DAMAGE_FACTOR
        return max(0.5, min(1.5, multiplier))

    def format_damage(self, result: DamageResult) -> dict:
        """格式化伤害显示：按伤害类型分类配色，暴击有特效，数字带浮动动画"""
        if result.is_dodge:
            return {
                "damage": 0,
                "is_crit": False,
                "is_dodge": True,
                "text": "miss",
                "color": "gray",
                "size": "normal",
                "effect": None,
                "float": True,
            }
        return {
            "damage": int(result.damage),
            "is_crit": result.is_crit,
            "is_dodge": False,
            "text": str(int(result.damage)),
            "color": self.type_colors.get(result.damage_type, "white"),
            "size": "large" if result.is_crit else "normal",
            "effect": "crit_burst" if result.is_crit else None,
            "float": True,
        }
