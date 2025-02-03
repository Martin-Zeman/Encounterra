#include "combatants/goblin.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "actions/action_types.hpp"

namespace enc
{

  Goblin::Goblin(int num) : Goblin(concatName(std::string(_className), num)) {}

  Goblin::Goblin(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, name, 7, 15, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::SMALL;

    addMeleeAttack("Scimitar", this,
                   4,                        // toHit
                   std::vector<Die>{{1, 6}}, // dmgDice
                   2,                        // dmgBonus
                   DamageType::Slashing,
                   1 // attackRange
    );

    auto shortbowFactory = addRangedAttack("Shortbow", this,
                                          4,                        // toHit
                                          std::vector<Die>{{1, 6}}, // dmgDice
                                          2,                        // dmgBonus
                                          DamageType::Piercing,
                                          64 // attackRange
    );
    setDangerZoneAttack(dynamic_cast<DirectThreatFactory *>(shortbowFactory));
  }

  ResourceState Goblin::exportResources()
  {
    // TODO
    return {};
  }
  void Goblin::importResources(const ResourceState &resources)
  {
    // TODO
  }
}