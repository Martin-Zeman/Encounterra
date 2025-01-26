#pragma once

#include <vector>
#include "effects/effect.hpp"

namespace enc
{
  class Combatant;

  class CombatantEffect : virtual public Effect
  {
  public:
    explicit CombatantEffect(Combatant *initiator, const std::vector<Combatant *> &combatants = {});

    bool isAffecting(const Combatant &combatant) const override;

    // Allow derived classes to access combatants
    const std::vector<Combatant *> &getCombatants() const;
    // std::vector<Combatant *> getCombatants() const;

  protected:
    std::vector<Combatant *> _combatants;
  };

} // namespace enc
