#include "core/rechargeable_factory.hpp"
#include "core/misc.hpp"
#include <iostream>

namespace enc
{
  void RechargeableFactory::rollForRecharge()
  {
    int roll = rollDice({1, 6});

    if(auto resource = getResource())
      {
        if(!(*resource)->hasUses() && roll >= _rechargeValue)
          {
            std::cout << _combatant.lock()->_name << "'s " << _name << " recharges" << std::endl;
            (*resource)->reset();
          }
      }
  }
}
