from abc import ABC, abstractmethod


class ActionPlanStrategy(ABC):

    def __init__(self, combatant):
        self.combatant = combatant
    @abstractmethod
    def calculate_action_plan(self, battle_map, distances, shortest_paths):
        return None
