#include "combatants/ogre.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  namespace
  {
    void buildOgre(Ogre *self)
    {
      self->setSize(Size::LARGE);

      auto greatclub = self->addMeleeAttack("Greatclub", self, 6, std::vector<Die>{{2, 8}}, 4, DamageType::Bludgeoning, 1);
      // Javelin: the single thrown javelin's ammo limit is not modelled (no ammo support in addRangedAttack).
      auto javelin = self->addRangedAttack("Javelin", self, 6, std::vector<Die>{{2, 6}}, 4, DamageType::Piercing, 24);
      self->addReactionAttack("Greatclub", self, 6, std::vector<Die>{{2, 8}}, 4, DamageType::Bludgeoning, 1);

      // Single attack: either the Greatclub or the Javelin (no multiattack).
      self->addAttackTransition(greatclub.get(), AttackFsm::START, AttackFsm::NOP);
      self->addAttackTransition(javelin.get(), AttackFsm::START, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, 4);
      self->setSavingThrow(SavingThrow::DEX, -1);
      self->setSavingThrow(SavingThrow::CON, 3);
      self->setSavingThrow(SavingThrow::INT, -3);
      self->setSavingThrow(SavingThrow::WIS, -2);
      self->setSavingThrow(SavingThrow::CHA, -2);
      self->setAthletics(4);
      self->setAcrobatics(-1);
    }
  }

  Ogre::Ogre(int num) : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, concatName(std::string(_className), num), 68, 11, -1, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    buildOgre(this);
  }

  Ogre::Ogre(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, name, 68, 11, -1, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    buildOgre(this);
  }
}