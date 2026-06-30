#include "warlock_lvl_4.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "effects/effect_tracker.hpp"

namespace enc
{
  namespace
  {
    void configureWarlockLvl4(WarlockLvl4 *self)
    {
      // Ability scores after the level-4 ASI into Charisma: STR 8 (-1), DEX 10 (+0), CON 15 (+2), INT 12 (+1),
      // WIS 14 (+2), CHA 18 (+4). Proficiency bonus +2. Proficient in Wisdom and Charisma saves.
      self->setSavingThrow(SavingThrow::STR, -1);
      self->setSavingThrow(SavingThrow::DEX, 0);
      self->setSavingThrow(SavingThrow::CON, 2);
      self->setSavingThrow(SavingThrow::INT, 1);
      self->setSavingThrow(SavingThrow::WIS, 4);  // 2 + proficiency 2
      self->setSavingThrow(SavingThrow::CHA, 6);  // 4 + proficiency 2
      self->setAthletics(-1);
      self->setAcrobatics(0);

      // Dagger (Finesse, Light): DEX (+0) with proficiency (+2) => +2 to hit, 1d4 Piercing. Reach 5 ft.
      auto dagger = self->addMeleeAttack("Dagger", self, 2, std::vector<Die>{{1, 4}}, 0, DamageType::Piercing, 1);
      self->addReactionAttack("Dagger", self, 2, std::vector<Die>{{1, 4}}, 0, DamageType::Piercing, 1);

      // Pact magic: two 2nd-level slots at level 4. Every leveled warlock spell upcasts to slot level 2.
      self->addSpellSlots();

      // Eldritch Blast + Agonizing Blast (now CHA +4 per beam).
      self->addEldritchBlast();
      self->addAgonizingBlast();

      // Hex / known leveled spells.
      self->addHex();
      self->addBane();
      self->addCharmPerson();
      self->addArmorOfAgathys();

      // Archfey always-prepared spells (Misty Step handled by Steps of the Fey below).
      self->addFaerieFire(self->getDC());
      self->addSleep();

      // Chosen leveled spell: Darkness (upcast to the 2nd-level pact slot).
      self->addDarkness();

      // Steps of the Fey: free Misty Step (uses = spellcasting modifier, now 4 per long rest).
      self->addStepsOfTheFey();

      // Devil's Sight invocation.
      self->addDevilsSight();

      // Armor of Shadows invocation: Mage Armor at will (base AC 13 + DEX 0).
      auto armorOfShadows = self->addArmorOfShadows(13);

      self->addAttackTransition(dagger.get(), AttackFsm::START, AttackFsm::NOP);

      // Enter combat with Armor of Shadows already cast.
      auto armorActoid = armorOfShadows->create(self);
      if(auto effect = std::dynamic_pointer_cast<Effect>(armorActoid))
        {
          EffectTracker::getInstance().add(effect);
          effect->activate();
        }
    }
  }

  WarlockLvl4::WarlockLvl4(int num)
      : Combatant(CombatantType::WARLOCK, Warlock::ARCHFEY_PATRON, _classLevel, concatName(std::string(_className), num), 31, 10, 0, 6, 30, 14)
  {
    _instanceId = generateInstanceId();
    configureWarlockLvl4(this);
  }

  WarlockLvl4::WarlockLvl4(const std::string &name)
      : Combatant(CombatantType::WARLOCK, Warlock::ARCHFEY_PATRON, _classLevel, name, 31, 10, 0, 6, 30, 14)
  {
    _instanceId = generateInstanceId();
    configureWarlockLvl4(this);
  }
}
