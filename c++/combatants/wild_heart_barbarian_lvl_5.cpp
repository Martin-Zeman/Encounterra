#include "combatants/wild_heart_barbarian_lvl_5.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  WildHeartBarbarianLvl5::WildHeartBarbarianLvl5(int num) : WildHeartBarbarianLvl5(concatName(std::string(_className), num)) {}

  WildHeartBarbarianLvl5::WildHeartBarbarianLvl5(const std::string &name)
      : Combatant(CombatantType::BARBARIAN, Barbarian::PATH_OF_WILD_HEART, _classLevel, name, 61, 15, 1, 0, 40, 15)
  {
    _instanceId = generateInstanceId();

    auto axeFactory = addMeleeAttack("Two-handed axe", this,
                                     7,                         // toHit
                                     std::vector<Die>{{1, 12}}, // dmgDice
                                     4,                         // dmgBonus
                                     DamageType::Slashing,
                                     1 // attackRange
    );

    addRangedAttack("Javelin", this,
                    7,                        // toHit
                    std::vector<Die>{{1, 6}}, // dmgDice
                    4,                        // dmgBonus
                    DamageType::Piercing,
                    24,                                 // attackRange
                    1,                                  // critRange
                    Uses(4, ResourceRefreshType::NEVER) // ammo
    );
    setDangerZoneAttack(dynamic_cast<DirectThreatFactory *>(axeFactory));
    setAoOFactory(dynamic_cast<AttackFactory *>(axeFactory));
  }

  ResourceState WildHeartBarbarianLvl5::exportResources()
  {
    // TODO
    return {};
  }
  void WildHeartBarbarianLvl5::importResources(const ResourceState &resources)
  {
    // TODO
  }
}