#pragma once

#include "effects/effect.hpp"

namespace enc
{
  class LimitedDurationEffect : virtual public Effect
  {
  public:
    LimitedDurationEffect(Combatant *initiator, int turns) : _turns(turns) {}

    bool startOfTurnTick() override;

  protected:
    int _turns;
  };
}
