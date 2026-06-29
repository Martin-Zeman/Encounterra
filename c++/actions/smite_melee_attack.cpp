#include "actions/smite_melee_attack.hpp"

#include "abilities/on_hit_divine_smite.hpp"

namespace enc
{
  SmiteMeleeAttackFactory::SmiteMeleeAttackFactory(const MeleeAttackFactory &base, const ActoidFactory *baseFactory)
      : MeleeAttackFactory(base), _baseFactory(baseFactory)
  {
    _abilityType = AbilityType::SMITE_MELEE_ATTACK;
    _name = "Smiting " + _name;
    addOnHit(std::make_unique<OnHitDivineSmite>());
  }
}
