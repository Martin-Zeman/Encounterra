#include "bugbear.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  // Monster Manual "Bugbear" statblock: Medium Humanoid (Goblinoid), AC 16, HP 27, Speed 30, Initiative +2.
  // Mirrors simulator/combatants/bugbear.py (the Python `test_bugbear` fixture) exactly:
  //  * Morningstar (Melee): +4 to hit, reach 5 ft. (1 square), 2d8+2 Piercing.
  //  * Javelin (Ranged): +4 to hit, 1d6+2 Piercing. (The Python port does not model javelin ammo, mirroring
  //    the other C++ thrown-weapon combatants, so it is registered as a plain ranged attack.)
  //  * Morningstar opportunity attack: +4 to hit, reach 5 ft. (1 square), 2d8+2 Piercing. addReactionAttack
  //    also registers this reach-5ft melee as the bugbear's danger-zone threat.
  //
  // Note: the printed bugbear has the "Long-Limbed" trait (reach +5 ft. on its own turn only). Python does not
  // model it, and neither do we; the opportunity-attack reach stays at 1 square, which is what governs the
  // rogue-kiting scenarios ported from the Python test suite.
  namespace
  {
    void buildBugbear(Bugbear *self)
    {
      auto morningstar = self->addMeleeAttack("Morningstar", self,
                                              4,                        // toHit
                                              std::vector<Die>{{2, 8}}, // dmgDice
                                              2,                        // dmgBonus
                                              DamageType::Piercing,
                                              1 // attackRange (reach 5 ft.)
      );

      auto javelin = self->addRangedAttack("Javelin", self,
                                           4,                        // toHit
                                           std::vector<Die>{{1, 6}}, // dmgDice
                                           2,                        // dmgBonus
                                           DamageType::Piercing,
                                           24 // attackRange
      );

      self->addAttackTransition(morningstar.get(), AttackFsm::START, AttackFsm::NOP);
      self->addAttackTransition(javelin.get(), AttackFsm::START, AttackFsm::NOP);

      self->addReactionAttack("Morningstar", self,
                              4,                        // toHit
                              std::vector<Die>{{2, 8}}, // dmgDice
                              2,                        // dmgBonus
                              DamageType::Piercing,
                              1 // attackRange (reach 5 ft.)
      );

      self->setSavingThrow(SavingThrow::STR, 2);
      self->setSavingThrow(SavingThrow::DEX, 2);
      self->setSavingThrow(SavingThrow::CON, 1);
      self->setSavingThrow(SavingThrow::INT, -1);
      self->setSavingThrow(SavingThrow::WIS, 0);
      self->setSavingThrow(SavingThrow::CHA, -1);

      self->setAthletics(2);
      self->setAcrobatics(2);
    }
  } // namespace

  Bugbear::Bugbear(int num)
      : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, concatName(std::string(_className), num), 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::MEDIUM;
    buildBugbear(this);
  }

  Bugbear::Bugbear(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, name, 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::MEDIUM;
    buildBugbear(this);
  }
}
