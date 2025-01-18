#pragma once

#include "effects/effect.hpp"

namespace enc
{
  class LimitedDurationEffect : virtual public Effect
  {
  public:
    LimitedDurationEffect(const std::shared_ptr<Combatant> &initiator, int turns) : Effect(initiator), _turns(turns) {}

    bool startOfTurnTick() override;

  protected:
    int _turns;
  };
}
