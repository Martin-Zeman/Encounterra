#include "core/spellslots.hpp"

namespace enc
{
  bool Spellslots::hasUses(int level) const
  {
    if(level == NO_LEVEL)
      {
        throw std::runtime_error("Must specify a spellslot level to use!");
      }
    return _currSpellslots.at(level) > 0;
  }

  int Spellslots::getUses(int level) const
  {
    if(level == NO_LEVEL)
      {
        throw std::runtime_error("Must specify a spellslot level to get!");
      }
    return _currSpellslots.at(level);
  }

  void Spellslots::useResource(int level)
  {
    if(_currSpellslots.find(level) != _currSpellslots.end())
      {
        _currSpellslots[level]--;
      }
    else
      {
        throw std::runtime_error("Invalid spell level");
      }
  }

  void Spellslots::reset() { _currSpellslots = _maxSpellslots; }

  void Spellslots::depleteResource(ResourceDepletionLevel level)
  {
    switch(level)
      {
      case ResourceDepletionLevel::FULLY_DEPLETED:
        for(auto &slot : _currSpellslots)
          {
            slot.second = 0;
          }
        break;
      case ResourceDepletionLevel::PARTIALLY_DEPLETED:
        for(auto &slot : _currSpellslots)
          {
            slot.second = _maxSpellslots[slot.first] / 2;
          }
        break;
      default: break;
      }
  }

  std::shared_ptr<Spellslots> spellslotFactory(CombatantType className, int classLevel)
  {
    const SpellslotTable *table = nullptr;

    switch(className)
      {
      case CombatantType::BARD:
      case CombatantType::CLERIC:
      case CombatantType::DRUID:
      case CombatantType::SORCERER:
      case CombatantType::WIZARD: table = &FULL_CASTER_TABLE; break;
      case CombatantType::PALADIN:
      case CombatantType::RANGER: table = &HALF_CASTER_TABLE; break;
      case CombatantType::FIGHTER:
      case CombatantType::ROGUE: table = &QUARTER_CASTER_TABLE; break;
      case CombatantType::WARLOCK: table = &WARLOCK_TABLE; break;
      default: return nullptr;
      }

    if(table && table->find(classLevel) != table->end())
      {
        return std::make_shared<Spellslots>((*table).at(classLevel));
      }

    return nullptr;
  }
}
