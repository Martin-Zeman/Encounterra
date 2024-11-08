#include "actions/ranged_attack.hpp"
#include "core/interfaces.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "effects/effect_tracker.hpp"

namespace enc
{
  RangedAttackFactory::RangedAttackFactory(const std::string &name, Combatant *combatant, AbilityType abilityType, int toHit,
                                           std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType, int attackRange, int critRange, Uses &&ammo,
                                           std::vector<std::unique_ptr<OnHit>> onHit, std::vector<DmgDieWithType> extraDmg, bool usesDex,
                                           bool twoHanded, Die toHitBonusDie)
      : AttackFactory(name, combatant, abilityType, toHit, dmgDice, dmgBonus, dmgType, attackRange, critRange, std::move(ammo), std::move(onHit),
                      extraDmg, usesDex, twoHanded, toHitBonusDie)
  {
    setFlag(FactoryFlags::IS_RANGED);
  }

  std::vector<std::shared_ptr<Actoid>> RangedAttackFactory::createAll(void *previousActionInDag)
  {
    auto eligibleTargets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(eligibleTargets.size());
    for(const auto &target : eligibleTargets)
      {
        result.push_back(std::make_shared<RangedAttack>(AbilityType::RANGED_ATTACK, *target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> RangedAttackFactory::create(void *target)
  {
    return std::make_shared<RangedAttack>(AbilityType::RANGED_ATTACK, *static_cast<Combatant *>(target), *this);
  }

  std::optional<std::vector<Coord>>
  RangedAttack::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    RangedAttackFactory &factory = dynamic_cast<RangedAttackFactory &>(getFactory());
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *swallower = factory._combatant->getSwallower();
    Coord currCoord = battleMap.getCombatantCoordinates(*factory._combatant).get()[0];

    if(swallower)
      {
        if(swallower == &_target)
          {
            return std::vector<Coord>{currCoord};
          }
        return {};
      }

    if(!factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        std::vector<Coord> freeCoordsInRange
          = battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(_target).get(), distances, factory._combatant->getSize(),
                                                    factory._attackRange, factory._combatant->_instanceId);

        if(!EffectTracker::getInstance().isCombatantHiddenFrom(factory._combatant, &_target))
          {
            std::vector<Coord> visibleCoords;
            std::copy_if(freeCoordsInRange.begin(), freeCoordsInRange.end(), std::back_inserter(visibleCoords),
                         [&battleMap, this](const Coord &coord) {
                           return battleMap.getVisibilityFromCoord(coord, &_target) != Visibility::NONE;
                         });
            return visibleCoords;
          }
        else
          {
            // We only consider the coords where Visibility::NONE transitions into any other kind
            std::vector<Coord> transitionCoords;
            for(const auto &coord : freeCoordsInRange)
              {
                if(battleMap.getVisibilityFromCoord(coord, &_target) != Visibility::NONE)
                  {
                    try
                      {
                        if(battleMap.getVisibilityFromCoord(shortestPaths(coord[0], coord[1]), &_target) == Visibility::NONE)
                          {
                            transitionCoords.push_back(coord);
                          }
                      }
                    catch(const std::out_of_range &)
                      {
                        transitionCoords.push_back(coord);
                      }
                  }
              }
            return transitionCoords;
          }
      }
    else if(battleMap.getCartesianDistanceCombatants(*factory._combatant, _target) <= factory._attackRange
            && battleMap.getVisibilityFromCoord(currCoord, &_target) != Visibility::NONE)
      {
        return std::vector<Coord>{currCoord};
      }

    return {};
  }
}