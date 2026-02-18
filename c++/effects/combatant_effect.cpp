#include "effects/combatant_effect.hpp"
#include <algorithm>

namespace enc
{
  CombatantEffect::CombatantEffect(Combatant* initiator, const std::vector<Combatant*>& combatants)
    : Effect(initiator),
      _combatants(combatants)
  {
  }

  bool CombatantEffect::isAffecting(Combatant* combatant) const
  {
    return std::find(_combatants.begin(), _combatants.end(), combatant) != _combatants.end();
  }

} // namespace enc
