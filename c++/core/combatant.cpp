#include "combatant.hpp"
#include "actions/dodge.hpp"
#include "actions/disengage.hpp"

namespace enc
{

  Combatant::Combatant(std::string name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc,
                       std::unordered_set<DamageType> resistances, std::unordered_set<DamageType> immunities,
                       std::unordered_set<DamageType> vulnerabities)
      : _name(name), _max_hp(hp), _curr_hp(hp), _ac(ac), _dc(dc), _init_bonus(init_bonus), _spell_to_hit(spell_to_hit), _speed(speed / 5),
        _movement(speed / 5), _resistances(resistances), _immunities(immunities), _vulnerabities(vulnerabities)
  {
    _dodge_factory = std::make_shared<DodgeFactory>();
    _disengage_factory = std::make_shared<DisengageFactory>();
    _action_factories.push_back(_dodge_factory);
    _action_factories.push_back(_disengage_factory); 
  }

  // Combatant::Combatant(std::string name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc,
  //                      std::unordered_set<DamageType> resistances = {}, std::unordered_set<DamageType> immunities = {},
  //                      std::unordered_set<DamageType> vulnerabities = {})
  //     : _name(name), _max_hp(hp), _curr_hp(hp), _ac(ac), _dc(dc), _init_bonus(init_bonus), _spell_to_hit(spell_to_hit), _speed(speed / 5),
  //       _movement(speed / 5), _resistances(resistances), _immunities(immunities), _vulnerabities(vulnerabities)
  // {
  //   _dodge_factory = std::make_shared<DodgeFactory>();
  //   _disengage_factory = std::make_shared<DisengageFactory>();
  //   _action_factories = {_dodge_factory, _disengage_factory};
  // }

  std::string Combatant::toString() const { return _name; }

  bool Combatant::isAlive() const { return _curr_hp > 0; }

  void Combatant::onDie()
  {
    // Implement functionality here...
  }

  void Combatant::onEndOfTurn() { _dmg_types_took_last_round.clear(); }

  void Combatant::rollInitiative()
  {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> distrib(1, 20);
    _curr_init = distrib(gen) + _init_bonus;
  }

}