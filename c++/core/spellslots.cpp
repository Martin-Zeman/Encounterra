#include "core/spellslots.hpp"

namespace enc
{
  bool Spellslots::hasResource(int level) { return currSpellslots[level] > 0; }

  int Spellslots::getResource(int level) { return currSpellslots[level]; }

  void Spellslots::useResource(int level)
  {
    if(currSpellslots.find(level) != currSpellslots.end())
      {
        currSpellslots[level]--;
      }
    else
      {
        throw std::runtime_error("Invalid spell level");
      }
  }

  void Spellslots::reset() { currSpellslots = maxSpellslots; }

  void Spellslots::depleteResource(ResourceDepletionLevel level)
  {
    switch(level)
      {
      case ResourceDepletionLevel::FULLY_DEPLETED:
        for(auto &slot : currSpellslots)
          {
            slot.second = 0;
          }
        break;
      case ResourceDepletionLevel::PARTIALLY_DEPLETED:
        for(auto &slot : currSpellslots)
          {
            slot.second = maxSpellslots[slot.first] / 2;
          }
        break;
      default: break;
      }
  }

  std::unique_ptr<Spellslots> spellslotFactory(Class className, int classLevel)
  {
    const SpellslotTable *table = nullptr;

    switch(className)
      {
      case Class::BARD:
      case Class::CLERIC:
      case Class::DRUID:
      case Class::SORCERER:
      case Class::WIZARD: table = &FULL_CASTER_TABLE; break;
      case Class::PALADIN:
      case Class::RANGER: table = &HALF_CASTER_TABLE; break;
      case Class::FIGHTER:
      case Class::ROGUE: table = &QUARTER_CASTER_TABLE; break;
      case Class::WARLOCK: table = &WARLOCK_TABLE; break;
      default: return nullptr;
      }

    if(table && table->find(classLevel) != table->end())
      {
        return std::make_unique<Spellslots>((*table).at(classLevel));
      }

    return nullptr;
  }
}
