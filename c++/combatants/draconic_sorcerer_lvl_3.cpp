#include "combatants/draconic_sorcerer_lvl_3.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  namespace
  {
    // Builds the 3rd-level Draconic Sorcerer's loadout (2024 rules). Stats (hp 23, ac 15, dc 13,
    // spell_to_hit 5) already bake in Draconic Resilience (+3 HP, unarmored AC 10 + Dex + Cha).
    void buildDraconicSorcererLvl3(DraconicSorcererLvl3 *self)
    {
      self->setSize(Size::MEDIUM);

      // Spellcasting resources first so spells can reference the shared spell-slot pool.
      self->addSpellSlots();
      self->addDraconicResilience();

      // Quarterstaff: a simple melee weapon used as both an action and an opportunity reaction.
      auto quarterstaff = self->addMeleeAttack("Quarterstaff", self, 1, std::vector<Die>{{1, 8}}, -1, DamageType::Bludgeoning, 1);
      self->addReactionAttack("Quarterstaff", self, 1, std::vector<Die>{{1, 8}}, -1, DamageType::Bludgeoning, 1);

      // Single attack: the quarterstaff (no multiattack).
      self->addAttackTransition(quarterstaff.get(), AttackFsm::START, AttackFsm::NOP);

      // Cantrips and leveled spells.
      auto firebolt = self->addFirebolt();
      self->addRayOfFrost();
      self->setDangerZoneAttack(static_cast<DirectThreatFactory *>(firebolt.get()));
      self->addScorchingRay();
      self->addHoldPerson();
      self->addMistyStep();
      self->addShield();

      // Class features.
      self->addInnateSorcery();
      self->addMetamagic();
      self->addQuickenedSpell(); // after the spells it can quicken and after addMetamagic()
      self->addTwinnedSpell();

      // Saving throws and skills.
      self->setSavingThrow(SavingThrow::STR, -1);
      self->setSavingThrow(SavingThrow::DEX, 2);
      self->setSavingThrow(SavingThrow::CON, 4);
      self->setSavingThrow(SavingThrow::INT, 1);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, 5);
      self->setAthletics(-1);
      self->setAcrobatics(2);
    }
  }

  DraconicSorcererLvl3::DraconicSorcererLvl3(int num)
      : Combatant(CombatantType::SORCERER, Sorcerer::DRACONIC_SORCERY, _classLevel, concatName(std::string(_className), num), 23, 15, 2, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    buildDraconicSorcererLvl3(this);
  }

  DraconicSorcererLvl3::DraconicSorcererLvl3(const std::string &name)
      : Combatant(CombatantType::SORCERER, Sorcerer::DRACONIC_SORCERY, _classLevel, name, 23, 15, 2, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    buildDraconicSorcererLvl3(this);
  }
}
