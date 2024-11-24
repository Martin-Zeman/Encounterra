#include "actions/melee_attack.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"

namespace enc
{
  MeleeAttackFactory::MeleeAttackFactory(const std::string &name, const std::string &abilityName, Combatant *combatant, AbilityType abilityType,
                                         int toHit, std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType, int attackRange, int critRange,
                                         Uses &&ammo, std::vector<std::unique_ptr<OnHit>> onHit, std::vector<DmgDieWithType> extraDmg, bool usesDex,
                                         bool twoHanded, Die toHitBonusDie)
      : AttackFactory(name, abilityName, combatant, abilityType, toHit, dmgDice, dmgBonus, dmgType, attackRange, critRange, std::move(ammo),
                      std::move(onHit), extraDmg, usesDex, twoHanded, toHitBonusDie)
  {
    setFlag(FactoryFlags::IS_MELEE);
  }

  std::vector<std::shared_ptr<Actoid>> MeleeAttackFactory::createAll(void *previousActionInDag)
  {
    auto eligibleTargets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(eligibleTargets.size());
    for(const auto &target : eligibleTargets)
      {
        result.push_back(std::make_shared<MeleeAttack>(AbilityType::MELEE_ATTACK, *target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> MeleeAttackFactory::create(void *target) { return std::make_shared<MeleeAttack>(AbilityType::MELEE_ATTACK, *static_cast<Combatant *>(target), *this); }

  std::optional<std::vector<Coord>>
  MeleeAttack::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    MeleeAttackFactory &factory = dynamic_cast<MeleeAttackFactory &>(getFactory());
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *swallower = factory._combatant->getSwallower();

    if(swallower)
      {
        if(swallower == &_target)
          {
            return std::vector<Coord>{battleMap.getCombatantCoordinates(*factory._combatant).getRoot()};
          }
        return {};
      }

    if(!factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInHopRange(battleMap.getCombatantCoordinates(_target).get(), distances, factory._combatant->getSize(),
                                                 factory._attackRange, factory._combatant->_instanceId);
      }
    else if(battleMap.getHopDistanceCombatants(*factory._combatant, _target) <= factory._attackRange)
      {
        return std::vector<Coord>{battleMap.getCombatantCoordinates(*factory._combatant).getRoot()};
      }

    return {};
  }
}