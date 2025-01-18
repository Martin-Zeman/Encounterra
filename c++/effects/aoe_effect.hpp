#pragma once

#include "effects/effect.hpp"
#include "core/interfaces.hpp"
#include <vector>

namespace enc
{
  class AoeEffect : virtual public Effect, public AoeThreat
  {
  public:
    explicit AoeEffect(const std::shared_ptr<Combatant> &initiator) : Effect(initiator) {}
    virtual ~AoeEffect() = default;

    // Pure virtual methods specific to AoeEffect
    virtual const CoordVector& getAffectedCoords() const = 0;
    virtual void onEnter(const std::shared_ptr<Combatant> &combatant) = 0;
    virtual void onMoveWithin(const std::shared_ptr<Combatant> &combatant) = 0;
    virtual void onExit(const std::shared_ptr<Combatant> &ombatant) = 0;
    virtual void onStartOfTurn(const std::shared_ptr<Combatant> &combatant) = 0;
    virtual void onEndOfTurn(const std::shared_ptr<Combatant> &combatant) = 0;

    // Concrete implementation of isAffecting from Effect base class
    bool isAffecting(const std::shared_ptr<Combatant> &combatant) const override;

  protected:
    // Add any protected members needed by derived classes
  };
}
