#include "core/resources.hpp"
#include "core/interfaces.hpp"
#include "core/combatant.hpp"
#include "actions/action_types.hpp"

namespace enc
{

  void useResources(Combatant *combatant, Actoid &actoid)
  {
    switch(actoid.getAbilityType())
      {
      case AbilityType::FIREBALL:
        if(auto resource = actoid.getFactory().getResource())
          {
            (*resource)->useResource(3);
          }
        else
          {
            throw std::runtime_error("Fireball factory must have an associated resource!");
          }
        combatant->setAlreadyUsedSpellslotThisTurn(true);
        break;

      case AbilityType::FIREBOLT: /*Nothing to do*/ break;

      default: break;
      }
  }

}
