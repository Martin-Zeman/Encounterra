#include "bugbear_warrior.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  // 2024 "Bugbear Warrior" statblock: Medium Fey (Goblinoid), AC 14, HP 33, Speed 30, Initiative +2.
  // STR 15(+2) DEX 14(+2) CON 13(+1) INT 8(-1) WIS 11(0) CHA 9(-1).
  //
  // Engine-adaptation notes (vs. the printed statblock):
  //  * "Grab" is a reach-10ft melee attack dealing 2d6+2 that, on a hit, applies the 2024 Grappled
  //    condition (escape DC 12). The grappled target can escape on its action with a Strength
  //    (Athletics) or Dexterity (Acrobatics) check.
  //  * The "Light Hammer" melee attacks gain Advantage against a creature the bugbear is grappling.
  //  * Skills (Stealth/Survival) and passive Perception have no effect in combat resolution and are
  //    not represented, but Athletics/Acrobatics are set so the bugbear can also escape grapples.
  namespace
  {
    void buildBugbearWarrior(BugbearWarrior *self)
    {
      // Grab: Melee, +4 to hit, reach 10 ft. (2 squares), 2d6+2 Bludgeoning, Grappled (escape DC 12).
      self->addGrappleAttack("Grab", self,
                             4,                        // toHit
                             std::vector<Die>{{2, 6}}, // dmgDice
                             2,                        // dmgBonus
                             DamageType::Bludgeoning,
                             2,  // attackRange (reach 10 ft.)
                             12, // grapple escape DC
                             SkillCheck::ATHLETICS);

      // Light Hammer (Melee): +4 to hit, reach 10 ft. (2 squares), 3d4+2 Bludgeoning.
      // Has Advantage against a creature the bugbear is grappling.
      auto lightHammer = self->addMeleeAttack("Light Hammer", self,
                                              4,                        // toHit
                                              std::vector<Die>{{3, 4}}, // dmgDice
                                              2,                        // dmgBonus
                                              DamageType::Bludgeoning,
                                              2 // attackRange (reach 10 ft.)
      );
      if(auto *lightHammerAttack = dynamic_cast<AttackFactory *>(lightHammer.get()))
        {
          lightHammerAttack->setAdvantageVsGrappledTarget(true);
        }

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

      // Athletics +2 (STR), Acrobatics +2 (DEX) — used when escaping a grapple.
      self->setAthletics(2);
      self->setAcrobatics(2);
    }
  } // namespace

  BugbearWarrior::BugbearWarrior(int num)
      : Combatant(CombatantType::MONSTER, Monster::FEY, _classLevel, concatName(std::string(_className), num), 33, 14, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::MEDIUM;
    buildBugbearWarrior(this);
  }

  BugbearWarrior::BugbearWarrior(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::FEY, _classLevel, name, 33, 14, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::MEDIUM;
    buildBugbearWarrior(this);
  }
}
