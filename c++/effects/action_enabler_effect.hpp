#pragma once

#include "effects/effect.hpp"

namespace enc
{
  class ActionEnablerEffect : virtual public Effect
  {
  public:
    explicit ActionEnablerEffect(Combatant *initiator, Combatant *target = nullptr) : Effect(initiator, target) {}

    virtual void enable() = 0;
    virtual void disable() = 0;
  };

} // namespace enc
