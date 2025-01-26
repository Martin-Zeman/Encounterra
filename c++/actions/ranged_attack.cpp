#include "actions/ranged_attack.hpp"
#include "core/interfaces.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "effects/effect_tracker.hpp"

namespace enc
{
  RangedAttackFactory::RangedAttackFactory(const std::string &name, const std::string &abilityName, Combatant& combatant, AbilityType abilityType,
                                           int toHit, std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType, int attackRange, int critRange,
                                           Uses &&ammo, std::vector<std::unique_ptr<OnHit>> onHit, std::vector<DmgDieWithType> extraDmg, bool usesDex,
                                           bool twoHanded, Die toHitBonusDie)
      : AttackFactory(name, abilityName, combatant, abilityType, toHit, dmgDice, dmgBonus, dmgType, attackRange, critRange, std::move(ammo),
                      std::move(onHit), extraDmg, usesDex, twoHanded, toHitBonusDie)
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
        result.push_back(std::make_shared<RangedAttack>(AbilityType::RANGED_ATTACK, *target.lock(), *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> RangedAttackFactory::create(void *target)
  {
    return std::make_shared<RangedAttack>(AbilityType::RANGED_ATTACK, *static_cast<Combatant *>(target), *this);
  }

  std::optional<CoordVector>
  RangedAttack::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    RangedAttackFactory &factory = dynamic_cast<RangedAttackFactory &>(getFactory());
    BattleMap &battleMap = BattleMap::getInstance();
    auto combatant = factory._combatant;
    Coord currCoord = battleMap.getCombatantCoordinates(*combatant).getRoot();

    if(Combatant *swallower = combatant->getSwallower())
      {
        if(*swallower == _target)
          {
            return CoordVector{currCoord};
          }
        return {};
      }

    if(!combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        CoordVector freeCoordsInRange
          = battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(_target).get(), distances, combatant->getSize(),
                                                    factory._attackRange, combatant->_instanceId);

        if(!EffectTracker::getInstance().isCombatantHiddenFrom(*combatant, _target))
          {
            CoordVector visibleCoords;
            std::copy_if(freeCoordsInRange.begin(), freeCoordsInRange.end(), std::back_inserter(visibleCoords),
                         [&battleMap, this](const Coord &coord) {
                           return battleMap.getVisibilityFromCoord(coord, _target) != Visibility::NONE;
                         });
            return visibleCoords;
          }
        else
          {
            // We only consider the coords where Visibility::NONE transitions into any other kind
            CoordVector transitionCoords;
            for(const auto &coord : freeCoordsInRange)
              {
                if(battleMap.getVisibilityFromCoord(coord, _target) != Visibility::NONE)
                  {
                    try
                      {
                        if(battleMap.getVisibilityFromCoord(shortestPaths(coord[0], coord[1]), _target) == Visibility::NONE)
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
    else if(battleMap.getCartesianDistanceCombatants(*combatant, _target) <= factory._attackRange
            && battleMap.getVisibilityFromCoord(currCoord, _target) != Visibility::NONE)
      {
        return CoordVector{currCoord};
      }

    return {};
  }

  size_t RangedAttack::hash() const
  {
    size_t h = std::hash<int>{}(static_cast<int>(getAbilityType()));
    h ^= std::hash<int>{}(static_cast<int>(getFlags())) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_target._instanceId) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<std::string>{}(_factory._name) + 0x9e3779b9 + (h << 6) + (h >> 2);
    return h;
  }

  bool RangedAttack::equals(const Actoid &other) const
  {
    if(auto *rangedAttack = dynamic_cast<const RangedAttack *>(&other))
      {
        return getAbilityType() == other.getAbilityType() && getFlags() == other.getFlags()
               && _target._instanceId == rangedAttack->_target._instanceId && _factory._name == rangedAttack->_factory._name;
      }
    return false;
  }
}