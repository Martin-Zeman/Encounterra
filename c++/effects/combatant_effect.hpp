#pragma once

#include <vector>
#include "effects/effect.hpp"

namespace enc
{
  class Combatant;

  class CombatantEffect : virtual public Effect
  {
  public:
    explicit CombatantEffect(Combatant* initiator, const std::vector<Combatant*>& combatants = {});
    
    bool isAffecting(Combatant* combatant) const override;
    
    // Allow derived classes to access combatants
    const std::vector<Combatant*>& getCombatants() const { return _combatants; }
    
  protected:
    std::vector<Combatant*> _combatants;
  };

} // namespace enc
