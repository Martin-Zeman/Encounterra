#include "combatants/goblin.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "actions/action_types.hpp"

namespace enc
{

  Goblin::Goblin(int num)
      : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, concatName(std::string(_className), num), 7, 15, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::SMALL;

    auto scimitar = addMeleeAttack("Scimitar", this,
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
    addReactionAttack("Scimitar", this,
                      4,                        // toHit
                      std::vector<Die>{{1, 6}}, // dmgDice
                      2,                        // dmgBonus
                      DamageType::Slashing,
                      1 // attackRange
    );
    setDangerZoneAttack(static_cast<DirectThreatFactory*>(shortbowFactory.get()));

    // Single attack: either the Scimitar or the Shortbow (no multiattack).
    addAttackTransition(scimitar.get(), AttackFsm::START, AttackFsm::NOP);
    addAttackTransition(shortbowFactory.get(), AttackFsm::START, AttackFsm::NOP);
  }

  Goblin::Goblin(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, name, 7, 15, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::SMALL;

    auto scimitar = addMeleeAttack("Scimitar", this,
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
    addReactionAttack("Scimitar", this,
                      4,                        // toHit
                      std::vector<Die>{{1, 6}}, // dmgDice
                      2,                        // dmgBonus
                      DamageType::Slashing,
                      1 // attackRange
    );
    setDangerZoneAttack(static_cast<DirectThreatFactory*>(shortbowFactory.get()));

    // Single attack: either the Scimitar or the Shortbow (no multiattack).
    addAttackTransition(scimitar.get(), AttackFsm::START, AttackFsm::NOP);
    addAttackTransition(shortbowFactory.get(), AttackFsm::START, AttackFsm::NOP);
  }
}