#include "combatant.hpp"

namespace enc
{

  Combatant::Combatant(int num_or_name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc,
                       std::unordered_set<std::string> resistances = {}, std::vector<std::string> immunities = {},
                       std::vector<std::string> vulnerabities = {})
      : name(nameFromNumber(num_or_name)), max_hp(hp), curr_hp(hp), ac(ac), dc(dc), init_bonus(init_bonus), spell_to_hit(spell_to_hit),
        speed(speed / 5), movement(speed / 5), resistances(resistances), immunities(immunities), vulnerabities(vulnerabities)
  {
    id = generateUniqueId(name, cls, level);

    // Initialize other member variables here...
    // action_factories.push_back({Action::DODGE, DodgeFactory(this)});
    // action_factories.push_back({Action::DISENGAGE, DisengageFactory(Action::DISENGAGE, this)});
    // dodge_factory = action_factories[0];
    // disengage_factory = action_factories[1];
    // ... more initializations
  }

  Combatant::Combatant(std::string num_or_name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc,
                       std::unordered_set<std::string> resistances = {}, std::vector<std::string> immunities = {},
                       std::vector<std::string> vulnerabities = {})
      : name(num_or_name), max_hp(hp), curr_hp(hp), ac(ac), dc(dc), init_bonus(init_bonus), spell_to_hit(spell_to_hit), speed(speed / 5),
        movement(speed / 5), resistances(resistances), immunities(immunities), vulnerabities(vulnerabities)
  {
    id = generateUniqueId(name, cls, level);

    // Initialize other member variables here...
  }

  std::string Combatant::toString() const { return name; }

  bool Combatant::isAlive() const { return curr_hp > 0; }

  void Combatant::onDie()
  {
    // Implement functionality here...
  }

  void Combatant::onEndOfTurn() { dmg_types_took_last_round.clear(); }

  void Combatant::rollInitiative()
  {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> distrib(1, 20);
    curr_init = distrib(gen) + init_bonus;
  }

  std::string Combatant::nameFromNumber(int num) { return "Combatant (" + std::to_string(num) + ")"; }
}