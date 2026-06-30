#include "warlock_lvl_1.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "effects/effect_tracker.hpp"

namespace enc
{
  namespace
  {
    void configureWarlockLvl1(WarlockLvl1 *self)
    {
      // Ability scores: STR 8 (-1), DEX 10 (+0), CON 15 (+2), INT 12 (+1), WIS 14 (+2), CHA 16 (+3).
      // Proficiency bonus +2. Warlocks are proficient in Wisdom and Charisma saves.
      self->setSavingThrow(SavingThrow::STR, -1);
      self->setSavingThrow(SavingThrow::DEX, 0);
      self->setSavingThrow(SavingThrow::CON, 2);
      self->setSavingThrow(SavingThrow::INT, 1);
      self->setSavingThrow(SavingThrow::WIS, 4);
      self->setSavingThrow(SavingThrow::CHA, 5);
      self->setAthletics(-1); // STR-based, not proficient
      self->setAcrobatics(0);  // DEX-based, not proficient

      // Dagger (Finesse, Light): uses the better of STR/DEX, so DEX (+0) with proficiency (+2) => +2 to hit,
      // 1d4 Piercing. Reach 5 ft.
      auto dagger = self->addMeleeAttack("Dagger", self, 2, std::vector<Die>{{1, 4}}, 0, DamageType::Piercing, 1);
      self->addReactionAttack("Dagger", self, 2, std::vector<Die>{{1, 4}}, 0, DamageType::Piercing, 1);

      // Pact magic: a single 1st-level slot (refreshed on a short rest). Drives Hex / Bane / Charm Person.
      self->addSpellSlots();

      // Eldritch Blast: signature cantrip (1d10 Force, 120 ft, single beam at level 1).
      self->addEldritchBlast();
      // Hex: bonus-action curse adding 1d6 Necrotic to the warlock's hits (concentration).
      self->addHex();
      // Leveled spells the warlock knows.
      self->addBane();
      self->addCharmPerson();

      // Armor of Shadows invocation: Mage Armor at will without a slot. Base AC while armored is 13 + DEX (0).
      auto armorOfShadows = self->addArmorOfShadows(13);

      self->addAttackTransition(dagger.get(), AttackFsm::START, AttackFsm::NOP);

      // The warlock enters combat with Armor of Shadows already cast: register and activate the effect so the
      // AC reflects Mage Armor (10 unarmored -> 13) from the very first turn, while the effect is present.
      auto armorActoid = armorOfShadows->create(self);
      if(auto effect = std::dynamic_pointer_cast<Effect>(armorActoid))
        {
          EffectTracker::getInstance().add(effect);
          effect->activate();
        }
    }
  }

  WarlockLvl1::WarlockLvl1(int num)
      : Combatant(CombatantType::WARLOCK, Warlock::FIEND_PATRON, _classLevel, concatName(std::string(_className), num), 10, 10, 0, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureWarlockLvl1(this);
  }

  WarlockLvl1::WarlockLvl1(const std::string &name)
      : Combatant(CombatantType::WARLOCK, Warlock::FIEND_PATRON, _classLevel, name, 10, 10, 0, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureWarlockLvl1(this);
  }
}
