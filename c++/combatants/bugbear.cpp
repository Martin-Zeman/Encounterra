#include "bugbear.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  Bugbear::Bugbear(int num) : Bugbear(concatName(std::string(_className), num)) {}

  Bugbear::Bugbear(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, name, 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();

    auto morningstarFactory = addMeleeAttack("Morningstar", this,
                                             4,                        // toHit
                                             std::vector<Die>{{2, 8}}, // dmgDice
                                             2,                        // dmgBonus
                                             DamageType::Piercing,
                                             1 // attackRange
    );

    addRangedAttack("Javelin", this,
                    4,                        // toHit
                    std::vector<Die>{{1, 6}}, // dmgDice
                    2,                        // dmgBonus
                    DamageType::Piercing,
                    24,                                 // attackRange
                    1,                                  // critRange
                    Uses(1, ResourceRefreshType::NEVER) // ammo
    );
    setDangerZoneAttack(dynamic_cast<DirectThreatFactory *>(morningstarFactory));
    setAoOFactory(dynamic_cast<AttackFactory *>(morningstarFactory));
  }

  ResourceState Bugbear::exportResources()
  {
    // TODO
    return {};
  }
  void Bugbear::importResources(const ResourceState &resources)
  {
    // TODO
  }
}