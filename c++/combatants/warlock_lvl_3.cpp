#include "warlock_lvl_3.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "effects/effect_tracker.hpp"

namespace enc
{
  namespace
  {
    void configureWarlockLvl3(WarlockLvl3 *self)
    {
      // Ability scores: STR 8 (-1), DEX 10 (+0), CON 15 (+2), INT 12 (+1), WIS 14 (+2), CHA 16 (+3).
      // Proficiency bonus +2. Warlocks are proficient in Wisdom and Charisma saves.
      self->setSavingThrow(SavingThrow::STR, -1);
      self->setSavingThrow(SavingThrow::DEX, 0);
      self->setSavingThrow(SavingThrow::CON, 2);
      self->setSavingThrow(SavingThrow::INT, 1);
      self->setSavingThrow(SavingThrow::WIS, 4);
      self->setSavingThrow(SavingThrow::CHA, 5);
      self->setAthletics(-1);
      self->setAcrobatics(0);

      // Dagger (Finesse, Light): DEX (+0) with proficiency (+2) => +2 to hit, 1d4 Piercing. Reach 5 ft.
      auto dagger = self->addMeleeAttack("Dagger", self, 2, std::vector<Die>{{1, 4}}, 0, DamageType::Piercing, 1);
      self->addReactionAttack("Dagger", self, 2, std::vector<Die>{{1, 4}}, 0, DamageType::Piercing, 1);

      // Pact magic: two 2nd-level slots at level 3. Every leveled warlock spell upcasts to slot level 2.
      self->addSpellSlots();

      // Eldritch Blast + Agonizing Blast (CHA +3 per beam).
      self->addEldritchBlast();
      self->addAgonizingBlast();

      // Hex / known leveled spells.
      self->addHex();
      self->addBane();
      self->addCharmPerson();
      self->addArmorOfAgathys();

      // Archfey always-prepared spells: Faerie Fire and Sleep (Misty Step is provided for free by Steps of the
      // Fey below, so it is not also added as a slot-spending action).
      self->addFaerieFire(self->getDC());
      self->addSleep();

      // Chosen leveled spell: Darkness (upcast to the 2nd-level pact slot).
      self->addDarkness();

      // Steps of the Fey (Archfey feature): free Misty Step a number of times per long rest equal to the
      // spellcasting modifier, with the Refreshing Step temporary-Hit-Point rider.
      self->addStepsOfTheFey();

      // Devil's Sight invocation (carried from level 2): never Blinded by magical Darkness.
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

  WarlockLvl3::WarlockLvl3(int num)
      : Combatant(CombatantType::WARLOCK, Warlock::ARCHFEY_PATRON, _classLevel, concatName(std::string(_className), num), 24, 10, 0, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureWarlockLvl3(this);
  }

  WarlockLvl3::WarlockLvl3(const std::string &name)
      : Combatant(CombatantType::WARLOCK, Warlock::ARCHFEY_PATRON, _classLevel, name, 24, 10, 0, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureWarlockLvl3(this);
  }
}
