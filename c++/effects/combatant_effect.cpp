#include "effects/combatant_effect.hpp"
#include <algorithm>

namespace enc
{
  CombatantEffect::CombatantEffect(const std::shared_ptr<Combatant> &initiator, const std::vector<std::shared_ptr<Combatant>> &combatants)
      : Effect(initiator)
  {
    // Convert shared_ptrs to weak_ptrs when storing
    _combatants.reserve(combatants.size());
    for(const auto &combatant : combatants)
      {
        _combatants.push_back(combatant);
      }
  }

  bool CombatantEffect::isAffecting(const std::shared_ptr<Combatant> &combatant) const
  {
    for(const auto &weakCombatant : _combatants)
      {
        if(auto storedCombatant = weakCombatant.lock())
          {
            if(storedCombatant == combatant)
              {
                return true;
              }
          }
      }
    return false;
  }

  std::vector<std::shared_ptr<Combatant>> CombatantEffect::getCombatants() const
  {
    std::vector<std::shared_ptr<Combatant>> result;
    result.reserve(_combatants.size());
    for(const auto &weakCombatant : _combatants)
      {
        if(auto combatant = weakCombatant.lock())
          {
            result.push_back(combatant);
          }
      }
    return result;
  }

} // namespace enc
