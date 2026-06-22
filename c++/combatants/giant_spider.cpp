#include "combatants/giant_spider.hpp"
#include "abilities/on_hit_saving_throw_dmg.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildGiantSpider(GiantSpider *self)
    {
      self->setSize(Size::LARGE);

      // Bite: +5, 1d8+3 Piercing, reach 5 ft., plus 2d6 Poison on a failed DC 13 Constitution save
      // (half on a success). The Web (Recharge 5-6) restrain, Spider Climb and Web Walker traits are
      // movement/control features without combat-simulation infrastructure and are omitted.
      std::vector<std::unique_ptr<OnHit>> biteRiders;
      biteRiders.push_back(std::make_unique<OnHitSavingThrowDmg>(SavingThrow::CON, 13, std::vector<Die>{{2, 6}}, DamageType::Poison, true, "Bite Venom"));
      auto bite = self->addMeleeAttackWithRiders("Bite", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Piercing, 1, std::move(biteRiders));

      // Opportunity attack uses the same Bite (no venom rider on the reaction, mirroring the Python reaction bite).
      self->addReactionAttack("Bite", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Piercing, 1);

      // Single attack: 0 -> nop.
      self->addAttackTransition(bite.get(), AttackFsm::START, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, 2);
      self->setSavingThrow(SavingThrow::DEX, 3);
      self->setSavingThrow(SavingThrow::CON, 1);
      self->setSavingThrow(SavingThrow::INT, -4);
      self->setSavingThrow(SavingThrow::WIS, 0);
      self->setSavingThrow(SavingThrow::CHA, -3);
      self->setAthletics(2);
      self->setAcrobatics(3);
    }
  }

  GiantSpider::GiantSpider(int num)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, concatName(std::string(_className), num), 26, 14, 3, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    buildGiantSpider(this);
  }

  GiantSpider::GiantSpider(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, name, 26, 14, 3, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    buildGiantSpider(this);
  }
}
