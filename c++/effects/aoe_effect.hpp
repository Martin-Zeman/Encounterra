#pragma once

#include "effects/effect.hpp"
#include "core/interfaces.hpp"
#include <vector>

namespace enc
{
  class AoeEffect : virtual public Effect, public AoeThreat
  {
  public:
    explicit AoeEffect(Combatant *initiator) : Effect(initiator) {}
    virtual ~AoeEffect() = default;

    // Pure virtual methods specific to AoeEffect
    virtual const CoordVector& getAffectedCoords() const = 0;
    virtual void onEnter(Combatant *combatant) = 0;
    virtual void onMoveWithin(Combatant *combatant) = 0;
    virtual void onExit(Combatant *combatant) = 0;
    virtual void onStartOfTurn(Combatant *combatant) = 0;
    virtual void onEndOfTurn(Combatant *combatant) = 0;

    // Concrete implementation of isAffecting from Effect base class
    bool isAffecting(Combatant *combatant) const override;

  protected:
    // Add any protected members needed by derived classes
  };
}
