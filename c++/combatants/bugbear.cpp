#include "bugbear.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  // 2024 "Bugbear Warrior" statblock: Medium Fey (Goblinoid), AC 14, HP 33, Speed 30, Initiative +2.
  // STR 15(+2) DEX 14(+2) CON 13(+1) INT 8(-1) WIS 11(0) CHA 9(-1).
  //
  // Engine-adaptation notes (vs. the printed statblock):
  //  * "Grab" is modelled as a reach-10ft melee attack dealing its 2d6+2 damage. The Grappled
  //    condition (escape DC 12) is NOT applied: the C++ resolver only deals damage on a hit and has
  //    no grapple resolution yet, so the rider is omitted rather than faked.
  //  * The two "Light Hammer" attacks gain Advantage when the target is Grappled by the bugbear. Since
  //    grappling is not modelled, those rolls resolve straight (no Advantage).
  //  * Skills (Stealth/Survival) and passive Perception have no effect in combat resolution and are
  //    not represented in the C++ Combatant.
  namespace
  {
    void buildBugbearWarrior(Bugbear *self)
    {
      // Grab: Melee, +4 to hit, reach 10 ft. (2 squares), 2d6+2 Bludgeoning.
      self->addMeleeAttack("Grab", self,
                           4,                        // toHit
                           std::vector<Die>{{2, 6}}, // dmgDice
                           2,                        // dmgBonus
                           DamageType::Bludgeoning,
                           2 // attackRange (reach 10 ft.)
      );

      // Light Hammer (Melee): +4 to hit, reach 10 ft. (2 squares), 3d4+2 Bludgeoning.
      self->addMeleeAttack("Light Hammer", self,
                           4,                        // toHit
                           std::vector<Die>{{3, 4}}, // dmgDice
                           2,                        // dmgBonus
                           DamageType::Bludgeoning,
                           2 // attackRange (reach 10 ft.)
      );

      // Light Hammer (Ranged): +4 to hit, range 20/60 ft., 3d4+2 Bludgeoning.
      self->addRangedAttack("Light Hammer (Thrown)", self,
                            4,                        // toHit
                            std::vector<Die>{{3, 4}}, // dmgDice
                            2,                        // dmgBonus
                            DamageType::Bludgeoning,
                            12 // attackRange (long range 60 ft.)
      );

      // Opportunity attack with the Light Hammer. addReactionAttack also registers this
      // reach-10ft melee as the bugbear's danger-zone threat. The bugbear is a melee
      // bruiser, so its projected threat is its reach rather than the backup thrown
      // hammer; we deliberately do NOT override the danger zone with the ranged attack.
      self->addReactionAttack("Light Hammer", self,
                             4,                        // toHit
                             std::vector<Die>{{3, 4}}, // dmgDice
                             2,                        // dmgBonus
                             DamageType::Bludgeoning,
                             2 // attackRange (reach 10 ft.)
      );

      self->setSavingThrow(SavingThrow::STR, 2);
      self->setSavingThrow(SavingThrow::DEX, 2);
      self->setSavingThrow(SavingThrow::CON, 1);
      self->setSavingThrow(SavingThrow::INT, -1);
      self->setSavingThrow(SavingThrow::WIS, 0);
      self->setSavingThrow(SavingThrow::CHA, -1);
    }
  } // namespace

  Bugbear::Bugbear(int num)
      : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, concatName(std::string(_className), num), 33, 14, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::MEDIUM;
    buildBugbearWarrior(this);
  }

  Bugbear::Bugbear(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, name, 33, 14, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::MEDIUM;
    buildBugbearWarrior(this);
  }
}