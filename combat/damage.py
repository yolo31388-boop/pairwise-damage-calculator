"""伤害计算战斗公式系统 - 存在bug"""
from dataclasses import dataclass, field
from typing import Optional
import random


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


@dataclass
class DamageResult:
    damage: float
    is_crit: bool = False
    is_dodge: bool = False
    damage_type: str = "physical"
    element: str = "physical"


class DamageCalculator:
    def __init__(self):
        self.element_advantage = {
            ("fire", "wind"): 1.5,
            ("water", "fire"): 1.5,
            ("earth", "water"): 1.5,
            ("wind", "earth"): 1.5,
        }

    def calculate_damage(self, attacker: CombatStats, defender: CombatStats) -> DamageResult:
        """计算伤害 - BUG: 只看攻击力不看防御力"""
        # BUG: 不计算防御力
        base_damage = attacker.attack
        # BUG: 不看属性克制
        # BUG: 不看等级差
        return DamageResult(damage=base_damage, damage_type=attacker.damage_type, element=attacker.element)

    def calculate_crit(self, attacker: CombatStats, defender: CombatStats) -> tuple[bool, float]:
        """计算暴击 - BUG: 只看暴击率不看暴击伤害"""
        # BUG: 不看暴击伤害，暴击和普通伤害一样
        is_crit = random.random() < attacker.crit_rate
        crit_multiplier = 1.0  # BUG: 不使用attacker.crit_damage
        return is_crit, crit_multiplier

    def calculate_dodge(self, attacker: CombatStats, defender: CombatStats) -> bool:
        """计算闪避 - BUG: 只看闪避率不看命中"""
        # BUG: 不看命中，100%闪避就是必闪
        return random.random() < defender.dodge_rate

    def apply_damage_type(self, damage: float, damage_type: str, defender: CombatStats) -> float:
        """应用伤害类型 - BUG: 只做物理和魔法"""
        # BUG: 不做实数和混沌伤害
        if damage_type == "physical":
            return max(0, damage - defender.defense)
        elif damage_type == "magic":
            return damage * 0.9  # 简单魔抗
        return damage

    def calculate_element_multiplier(self, attacker_element: str, defender_element: str) -> float:
        """计算属性克制倍率"""
        return self.element_advantage.get((attacker_element, defender_element), 1.0)

    def calculate_level_difference(self, attacker_level: int, defender_level: int) -> float:
        """计算等级差倍率 - BUG: 不实现"""
        # BUG: 不实现，总是返回1.0
        return 1.0

    def format_damage(self, result: DamageResult) -> dict:
        """格式化伤害显示 - BUG: 不做分类"""
        # BUG: 不做分类，所有伤害一个颜色
        return {
            "damage": int(result.damage),
            "is_crit": result.is_crit,
            "color": "white",  # BUG: 不区分伤害类型
        }
