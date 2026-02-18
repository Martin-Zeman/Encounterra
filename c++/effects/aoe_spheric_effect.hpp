#pragma once

#include "effects/spheric_aoe.hpp"
#include "effects/aoe_effect.hpp"

namespace enc
{
  class AoeSphericEffect : public SphericAoe, virtual public AoeEffect
  {
  public:
    AoeSphericEffect(Combatant *initiator, const Coord &coord, int radius) : SphericAoe(coord, radius), AoeEffect(initiator) {}
  };
}
