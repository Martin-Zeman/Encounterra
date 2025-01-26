#pragma once

#include "core/interfaces.hpp"
#include "core/combatant.hpp"

namespace enc
{

  class RechargeableFactory : public ActoidFactory
  {
  protected:
    int _rechargeValue;

  public:
    RechargeableFactory(const std::string &name, const std::string &abilityName, Combatant& combatant, AbilityType abilityType, int rechargeValue)
        : ActoidFactory(name, abilityName, combatant, abilityType), _rechargeValue(rechargeValue)
    {
      setFlag(FactoryFlags::IS_RECHARGE);
    }

    void rollForRecharge();
  };
}
