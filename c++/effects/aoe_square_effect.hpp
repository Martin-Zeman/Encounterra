#pragma once

#include "effects/square_aoe.hpp"
#include "effects/aoe_effect.hpp"

namespace enc
{
  class AoeSquareEffect : public SquareAoe, virtual public AoeEffect
  {
  public:
    AoeSquareEffect(Combatant *initiator, const Coord &origin, int length) : SquareAoe(origin, length), AoeEffect(initiator) {}

    // void activate(const Kwargs &kwargs = {}) override
    // {
    //   // Implementation
    // }

    // void deactivate() override
    // {
    //   // Implementation
    // }

    // bool deactivateForCombatant(Combatant &combatant) override
    // {
    //   // Implementation
    //   return true;
    // }

    // // Override isAffecting from AoeEffect
    // bool isAffecting(Combatant *combatant) const override
    // {
    //   return false; // TODO: Implement proper logic
    // }

    // // Implement pure virtual methods from AoeEffect
    // CoordVector getAffectedCoords() const override { return SquareAoe::getAffectedCoords(); }

    // void onEnter(Combatant *combatant) override
    // {
    //   // Implementation
    // }

    // void onMoveWithin(Combatant *combatant) override
    // {
    //   // Implementation
    // }

    // void onExit(Combatant *combatant) override
    // {
    //   // Implementation
    // }

    // void onStartOfTurn(Combatant *combatant) override
    // {
    //   // Implementation
    // }

    // void onEndOfTurn(Combatant *combatant) override
    // {
    //   // Implementation
    // }
  };
}
