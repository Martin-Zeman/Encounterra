#include "combatants/moon_druid_lvl_3.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  namespace
  {
    // Builds the 3rd-level Circle of the Moon Druid's loadout (2024 rules). Stats (hp 27, ac 13, dc 13,
    // spell_to_hit 5) match simulator/combatants/moon_druid_3lvl.py. The druid's leveled spells are flagged
    // TRANSITIONS_TO_WILDSHAPE so they remain castable while the druid is in beast form (user override).
    void buildMoonDruidLvl3(MoonDruidLvl3 *self)
    {
      self->setSize(Size::MEDIUM);

      // Spellcasting resources first so spells can reference the shared spell-slot pool.
      self->addSpellSlots();

      // Scimitar: melee weapon used as both an action and an opportunity reaction. It is also the
      // combatant's danger-zone (reach) attack.
      auto scimitar = self->addMeleeAttack("Scimitar", self, 3, std::vector<Die>{{1, 6}}, 1, DamageType::Slashing, 1);
      self->addReactionAttack("Scimitar", self, 3, std::vector<Die>{{1, 6}}, 1, DamageType::Slashing, 1);
      self->setDangerZoneAttack(static_cast<DirectThreatFactory *>(scimitar.get()));

      // Longbow: ranged weapon (120 ft = 24 cells).
      auto longbow = self->addRangedAttack("Longbow", self, 3, std::vector<Die>{{1, 8}}, 1, DamageType::Piercing, 24);

      // Single attack per turn: either the scimitar or the longbow.
      self->addAttackTransition(scimitar.get(), AttackFsm::START, AttackFsm::NOP);
      self->addAttackTransition(longbow.get(), AttackFsm::START, AttackFsm::NOP);

      // Leveled spells. Flag each as TRANSITIONS_TO_WILDSHAPE so they survive the Wild Shape stash.
      auto flamingSphere = self->addFlamingSphere(13);
      auto holdPerson = self->addHoldPerson();
      auto faerieFire = self->addFaerieFire(13);
      auto spikeGrowth = self->addSpikeGrowth();
      auto thunderwave = self->addThunderwave(13);
      auto healingWord = self->addHealingWord();
      for(auto &spell : {flamingSphere, holdPerson, faerieFire, spikeGrowth, thunderwave, healingWord})
        {
          spell->setFlag(FactoryFlags::TRANSITIONS_TO_WILDSHAPE);
        }

      // Class feature: Circle of the Moon Wild Shape.
      self->addMoonWildshape();

      // Saving throws and skills.
      self->setSavingThrow(SavingThrow::STR, 0);
      self->setSavingThrow(SavingThrow::DEX, 1);
      self->setSavingThrow(SavingThrow::CON, 3);
      self->setSavingThrow(SavingThrow::INT, 4);
      self->setSavingThrow(SavingThrow::WIS, 5);
      self->setSavingThrow(SavingThrow::CHA, 1);
      self->setAthletics(1);
      self->setAcrobatics(1);
    }
  }

  MoonDruidLvl3::MoonDruidLvl3(int num)
      : Combatant(CombatantType::DRUID, Druid::CIRCLE_OF_MOON, _classLevel, concatName(std::string(_className), num), 27, 13, 1, 5, 35, 13)
  {
    _instanceId = generateInstanceId();
    buildMoonDruidLvl3(this);
  }

  MoonDruidLvl3::MoonDruidLvl3(const std::string &name)
      : Combatant(CombatantType::DRUID, Druid::CIRCLE_OF_MOON, _classLevel, name, 27, 13, 1, 5, 35, 13)
  {
    _instanceId = generateInstanceId();
    buildMoonDruidLvl3(this);
  }
}
