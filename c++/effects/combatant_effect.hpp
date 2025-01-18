#pragma once

#include <vector>
#include "effects/effect.hpp"

namespace enc
{
  class Combatant;

  class CombatantEffect : virtual public Effect
  {
  public:
    explicit CombatantEffect(const std::shared_ptr<Combatant> &initiator, const std::vector<std::shared_ptr<Combatant>> &combatants = {});

    bool isAffecting(const std::shared_ptr<Combatant> &combatant) const override;

    // Allow derived classes to access combatants
    std::vector<std::shared_ptr<Combatant>> getCombatants() const;

  protected:
    std::vector<std::weak_ptr<Combatant>> _combatants;
  };

} // namespace enc
