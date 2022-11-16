from simulator.combat_manager import *

class RoundManager:
    def __init__(self, characters, battle_map, combat_manager, num_rounds = 20):
        self.characters = characters
        self.num_rounds = num_rounds
        self.battle_map = battle_map
        self.combat_manager = combat_manager

    def order_by_initiative(self):
        def by_initiative(e):
            return e.curr_init

        self.characters.sort(key=by_initiative, reverse=True)
        print("--------------INITIATIVE ORDER--------------")
        for character in self.characters:
            print(f"{character.get_name()} with {character.get_curr_init()}")

    def is_only_one_team_standing(self):
        team_head_count = {}
        for character in self.characters:
            if character.is_alive():
                try:
                    team_head_count[character.get_team()] += 1
                except KeyError:
                    team_head_count[character.get_team()] = 1
        num_teams_standing = 0
        for key, val in team_head_count.items():
            if val:
                num_teams_standing += 1
                if num_teams_standing > 1:
                    return False
        return True

    def simulate(self):
        self.order_by_initiative()
        print("--------------START--------------")
        for r in range(self.num_rounds):
            print(f"Round {r + 1}:")
            if self.is_only_one_team_standing():
                print("EARLY END")
                return
            for character in self.characters:
                if character.is_alive():
                    character.new_round()
                    while True:
                        action = character.get_action(self.battle_map)
                        if action is None:
                            break
                        self.combat_manager.resolve_action(action)
                    # if (self.is_only_one_team_standing()):
                    #     print("EARLY END")
                    #     return
                else:
                    print(f"Character {character.get_name()} is dead. Skipping")
            self.print_status()

    def print_status(self):
        for character in self.characters:
            status = f"alive with {character.get_curr_hp()}" if character.is_alive() else "dead"
            print(f"Character {character.get_name()} is {status}")

    def print_results(self):
        print("--------------RESULT--------------")
        self.print_status()

