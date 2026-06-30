#include "warlock_lvl_2.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "effects/effect_tracker.hpp"

namespace enc
{
  namespace
  {
    void configureWarlockLvl2(WarlockLvl2 *self)
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

      // Pact magic: two 1st-level slots at level 2 (refreshed on a short rest).
      self->addSpellSlots();

      // Eldritch Blast + Agonizing Blast: signature cantrip, now adding CHA (+3) to each beam's damage.
      self->addEldritchBlast();
      self->addAgonizingBlast();

      // Hex / known leveled spells.
      self->addHex();
      self->addBane();
      self->addCharmPerson();
      // Armor of Agathys: bonus-action self-buff, temporary Hit Points + Cold retaliation, upcast to the pact
      // slot level.
      self->addArmorOfAgathys();

      // Devil's Sight invocation: never Blinded by magical Darkness.
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

  WarlockLvl2::WarlockLvl2(int num)
      : Combatant(CombatantType::WARLOCK, Warlock::FIEND_PATRON, _classLevel, concatName(std::string(_className), num), 17, 10, 0, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureWarlockLvl2(this);
  }

  WarlockLvl2::WarlockLvl2(const std::string &name)
      : Combatant(CombatantType::WARLOCK, Warlock::FIEND_PATRON, _classLevel, name, 17, 10, 0, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureWarlockLvl2(this);
  }
}
