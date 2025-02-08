#include "combatants/wild_heart_barbarian_lvl_3.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  WildHeartBarbarianLvl3::WildHeartBarbarianLvl3(int num) : WildHeartBarbarianLvl3(concatName(std::string(_className), num)) {}

  WildHeartBarbarianLvl3::WildHeartBarbarianLvl3(const std::string &name)
      : Combatant(CombatantType::BARBARIAN, Barbarian::PATH_OF_WILD_HEART, _classLevel, name, 35, 14, 1, 0, 30, 13)
  {
    _instanceId = generateInstanceId();

    auto axeFactory = addMeleeAttack("Two-handed axe", this,
                                     5,                         // toHit
                                     std::vector<Die>{{1, 12}}, // dmgDice
                                     3,                         // dmgBonus
                                     DamageType::Slashing,
                                     1 // attackRange
    );

    addRangedAttack("Javelin", this,
                    5,                        // toHit
                    std::vector<Die>{{1, 6}}, // dmgDice
                    3,                        // dmgBonus
                    DamageType::Piercing,
                    24,                                 // attackRange
                    1,                                  // critRange
                    Uses(4, ResourceRefreshType::NEVER) // ammo
    );
    setDangerZoneAttack(dynamic_cast<DirectThreatFactory *>(axeFactory));
    setAoOFactory(dynamic_cast<AttackFactory *>(axeFactory));
  }

  ResourceState WildHeartBarbarianLvl3::exportResources()
  {
    // TODO
    return {};
  }
  void WildHeartBarbarianLvl3::importResources(const ResourceState &resources)
  {
    // TODO
  }
}