#include "combatant.hpp"
#include "actions/dodge.hpp"
#include "actions/disengage.hpp"

namespace enc
{

  Combatant::Combatant(std::string name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc,
                       std::unordered_set<DamageType> resistances, std::unordered_set<DamageType> immunities,
                       std::unordered_set<DamageType> vulnerabities)
      : _name(name), _maxHp(hp), _currHp(hp), _ac(ac), _dc(dc), _initBonus(init_bonus), _spellToHit(spell_to_hit), _speed(speed / 5),
        _movement(speed / 5), _resistances(resistances), _immunities(immunities), _vulnerabities(vulnerabities)
  {
    _dodgeFactory = std::make_shared<DodgeFactory>();
    _disengageFactory = std::make_shared<DisengageFactory>();
    _actionFactories.push_back(_dodgeFactory);
    _actionFactories.push_back(_disengageFactory);
  }

  // Combatant::Combatant(std::string name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc,
  //                      std::unordered_set<DamageType> resistances = {}, std::unordered_set<DamageType> immunities = {},
  //                      std::unordered_set<DamageType> vulnerabities = {})
  //     : _name(name), _maxHp(hp), _currHp(hp), _ac(ac), _dc(dc), _initBonus(init_bonus), _spellToHit(spell_to_hit), _speed(speed / 5),
  //       _movement(speed / 5), _resistances(resistances), _immunities(immunities), _vulnerabities(vulnerabities)
  // {
  //   _dodgeFactory = std::make_shared<DodgeFactory>();
  //   _disengageFactory = std::make_shared<DisengageFactory>();
  //   _actionFactories = {_dodgeFactory, _disengageFactory};
  // }

  std::string Combatant::toString() const { return _name; }

  bool Combatant::isAlive() const { return _currHp > 0; }

  void Combatant::onDie()
  {
    // Implement functionality here...
  }

  void Combatant::onEndOfTurn() { _dmgTypesTookLastRound.clear(); }

  void Combatant::rollInitiative()
  {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> distrib(1, 20);
    _currInit = distrib(gen) + _initBonus;
  }

  Combatant *Combatant::getCurrentForm() { return _currentWildshapeForm == nullptr ? _originalForm : _currentWildshapeForm; }
  Combatant *Combatant::getOriginalForm() { return _originalForm; }

  bool Combatant::hasCondition(Conditions condition) const
  {
    return std::any_of(_conditions.begin(), _conditions.end(), [condition](const Condition &c) { return hasCondition(c.conditions, condition); })
           || std::any_of(_dcConditions.begin(), _dcConditions.end(),
                          [condition](const ConditionWithDC &c) { return hasCondition(c.conditions, condition); });
  }

  void Combatant::addCondition(const Condition &condition)
  {
    _conditions.push_back(condition);
    if(hasCondition(condition.conditions, Conditions::SWALLOWED))
      {
        _swallower = condition.initiator;
      }
  }

  void Combatant::addDCCondition(const ConditionWithDC &condition)
  {
    _dcConditions.push_back(condition);
    if(hasCondition(condition.conditions, Conditions::SWALLOWED))
      {
        _swallower = condition.initiator;
      }
  }

  bool Combatant::removeCondition(Conditions condition, const Combatant *initiator = nullptr)
  {
    auto it = std::find_if(_conditions.begin(), _conditions.end(), [condition, initiator](const Condition &c) {
      return hasCondition(c.conditions, condition) && (!initiator || c.initiator == initiator);
    });
    if(it != _conditions.end())
      {
        _conditions.erase(it);
        if(condition == Conditions::SWALLOWED)
          {
            _swallower = nullptr;
          }
        return true;
      }
    return false;
  }

  bool Combatant::removeDCCondition(Conditions condition, const Combatant *initiator = nullptr)
  {
    auto it = std::find_if(_dcConditions.begin(), _dcConditions.end(), [condition, initiator](const ConditionWithDC &c) {
      return hasCondition(c.conditions, condition) && (!initiator || c.initiator == initiator);
    });
    if(it != _dcConditions.end())
      {
        _dcConditions.erase(it);
        if(condition == Conditions::SWALLOWED)
          {
            _swallower = nullptr;
          }
        return true;
      }
    return false;
  }
}