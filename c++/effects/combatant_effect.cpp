#include "effects/combatant_effect.hpp"
#include <algorithm>

namespace enc
{
  CombatantEffect::CombatantEffect(Combatant *initiator, const std::vector<Combatant *> &combatants) : Effect(initiator)
  {
    // Convert shared_ptrs to weak_ptrs when storing
    _combatants.reserve(combatants.size());
    for(const auto &combatant : combatants)
      {
        _combatants.push_back(combatant);
      }
  }

  bool CombatantEffect::isAffecting(const Combatant &combatant) const
  {
    for(const auto &cbt : _combatants)
      {
        if(*cbt == combatant)
          {
            return true;
          }
      }
    return false;
  }

  const std::vector<Combatant *> &CombatantEffect::getCombatants() const { return _combatants; }

  // std::vector<Combatant *> CombatantEffect::getCombatants() const
  // {
  //   std::vector<Combatant *> result;
  //   result.reserve(_combatants.size());
  //   for(const auto &combatant : _combatants)
  //     {
  //       result.push_back(combatant);
  //     }
  //   return result;
  // }

} // namespace enc
