#include "core/resources.hpp"
#include "core/interfaces.hpp"
#include "actions/action_types.hpp"

namespace enc
{

  void useResources(Combatant *combatant, Actoid& actoid){
    switch (actoid.getAbilityType())
    {
    case AbilityType::FIREBALL:
        actoid.getFactory().getResource().useResource(3);
        combatant->setAlreadyUsedSpellslotThisTurn(true);
        break;
    
    default:
        break;
    }
  }

}
