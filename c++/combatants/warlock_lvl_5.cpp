#include "warlock_lvl_5.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "effects/effect_tracker.hpp"

namespace enc
{
  namespace
  {
    void configureWarlockLvl5(WarlockLvl5 *self)
    {
      // Ability scores: STR 8 (-1), DEX 10 (+0), CON 15 (+2), INT 12 (+1), WIS 14 (+2), CHA 18 (+4).
      // Proficiency bonus +3 at level 5. Proficient in Wisdom and Charisma saves.
      self->setSavingThrow(SavingThrow::STR, -1);
      self->setSavingThrow(SavingThrow::DEX, 0);
      self->setSavingThrow(SavingThrow::CON, 2);
      self->setSavingThrow(SavingThrow::INT, 1);
      self->setSavingThrow(SavingThrow::WIS, 5);  // 2 + proficiency 3
      self->setSavingThrow(SavingThrow::CHA, 7);  // 4 + proficiency 3
      self->setAthletics(-1);
      self->setAcrobatics(0);

      // Dagger (Finesse, Light): DEX (+0) with proficiency (+3) => +3 to hit, 1d4 Piercing. Reach 5 ft.
      auto dagger = self->addMeleeAttack("Dagger", self, 3, std::vector<Die>{{1, 4}}, 0, DamageType::Piercing, 1);
      self->addReactionAttack("Dagger", self, 3, std::vector<Die>{{1, 4}}, 0, DamageType::Piercing, 1);

      // Pact magic: two 3rd-level slots at level 5. Every leveled warlock spell upcasts to slot level 3.
      self->addSpellSlots();

      // Eldritch Blast: two beams at level 5. Agonizing Blast (CHA +4) and Repelling Blast (push on hit).
      self->addEldritchBlast();
      self->addAgonizingBlast();
      self->addRepellingBlast();

      // Hex / known leveled spells.
      self->addHex();
      self->addBane();
      self->addCharmPerson();
      self->addArmorOfAgathys();

      // Archfey always-prepared spells (Misty Step handled by Steps of the Fey below).
      self->addFaerieFire(self->getDC());
      self->addSleep();

      // Leveled spells (all upcast to the 3rd-level pact slot): Darkness, Hypnotic Pattern and Blink.
      self->addDarkness();
      self->addHypnoticPattern();
      self->addBlink();

      // Steps of the Fey: free Misty Step (uses = spellcasting modifier, 4 per long rest).
      self->addStepsOfTheFey();

      // Invocations: Devil's Sight and Eldritch Mind (Advantage on Concentration saves).
      self->addDevilsSight();
      self->addEldritchMind();

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

  WarlockLvl5::WarlockLvl5(int num)
      : Combatant(CombatantType::WARLOCK, Warlock::ARCHFEY_PATRON, _classLevel, concatName(std::string(_className), num), 38, 10, 0, 7, 30, 15)
  {
    _instanceId = generateInstanceId();
    configureWarlockLvl5(this);
  }

  WarlockLvl5::WarlockLvl5(const std::string &name)
      : Combatant(CombatantType::WARLOCK, Warlock::ARCHFEY_PATRON, _classLevel, name, 38, 10, 0, 7, 30, 15)
  {
    _instanceId = generateInstanceId();
    configureWarlockLvl5(this);
  }
}
