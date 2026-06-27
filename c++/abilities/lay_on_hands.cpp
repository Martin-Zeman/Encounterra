#include "abilities/lay_on_hands.hpp"

#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/teams.hpp"
#include <algorithm>

namespace enc
{
  LayOnHandsFactory::LayOnHandsFactory(Combatant *combatant, Resource *resource)
      : DirectThreatFactory("LayOnHandsFactory", "Lay on Hands", combatant, AbilityType::LAY_ON_HANDS), _resource(resource)
  {}

  std::vector<Combatant *> LayOnHandsFactory::getEligibleTargets() const
  {
    if(_combatant->getSwallower())
      {
        return {};
      }

    std::vector<Combatant *> targets;
    if(!_combatant->isAlive())
      {
        return targets;
      }
    targets.push_back(_combatant);

    for(auto *ally : BattleMap::getInstance().getNonSwallowedAlliesWithinRadius(_combatant, range))
      {
        if(ally != _combatant)
          {
            targets.push_back(ally);
          }
      }
    return targets;
  }

  std::vector<std::shared_ptr<Actoid>> LayOnHandsFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    if(!_resource->hasUses())
      {
        return result;
      }

    for(auto *target : getEligibleTargets())
      {
        int missingHp = std::max(0, target->getMaxHp() - target->getCurrentHp());
        int hpAmount = std::min(missingHp, _resource->getUses());
        if(hpAmount > 0)
          {
            result.push_back(std::make_shared<LayOnHands>(*target, *this, hpAmount));
          }
        if(target->isAffectedBy(Conditions::POISONED) && _resource->getUses() >= poisonedRemovalCost)
          {
            result.push_back(std::make_shared<LayOnHands>(*target, *this, 0, true));
          }
      }
    return result;
  }

  std::shared_ptr<Actoid> LayOnHandsFactory::create(void *target)
  {
    auto *combatant = static_cast<Combatant *>(target);
    int missingHp = std::max(0, combatant->getMaxHp() - combatant->getCurrentHp());
    int hpAmount = _resource->hasUses() ? std::min(missingHp, _resource->getUses()) : 0;
    return std::make_shared<LayOnHands>(*combatant, *this, hpAmount);
  }

  std::shared_ptr<Actoid> LayOnHandsFactory::createPoisonRemoval(Combatant *target)
  {
    return std::make_shared<LayOnHands>(*target, *this, 0, true);
  }

  double LayOnHandsFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    if(target->getSwallower() || !target->isAlive() || !_resource->hasUses())
      {
        return 0.0;
      }
    if(target != _combatant && BattleMap::getInstance().getCartesianDistanceCombatants(*_combatant, *target) > range)
      {
        return 0.0;
      }

    int hpAmount = _resource->getUses();
    if(kwargs.find("hp_amount") != kwargs.end())
      {
        hpAmount = std::any_cast<int>(kwargs.at("hp_amount"));
      }
    int missingHp = std::max(0, target->getMaxHp() - target->getCurrentHp());
    double threat = std::min(missingHp, hpAmount);
    if(target->isAffectedBy(Conditions::POISONED) && _resource->getUses() >= poisonedRemovalCost)
      {
        threat += poisonedRemovalCost;
      }
    return threat;
  }

  double LayOnHandsFactory::calculateMaxThreat() const
  {
    return _resource->hasUses() ? static_cast<double>(_resource->getUses()) : 0.0;
  }

  std::string LayOnHands::toString() const
  {
    if(_removePoison)
      {
        return "Lay on Hands removes Poisoned from " + _target._name;
      }
    return "Lay on Hands for " + std::to_string(_hpAmount) + " HP on " + _target._name;
  }

  std::string LayOnHands::shorthandStr() const { return "Lay on Hands"; }

  double LayOnHands::calculateThreat(const Kwargs &kwargs)
  {
    Kwargs local = kwargs;
    local["hp_amount"] = _hpAmount;
    return _factory.calculateThreatToTarget(&_target, local);
  }

  double LayOnHands::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0.0; }

  std::optional<CoordVector>
  LayOnHands::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(_factory._combatant->getSwallower())
      {
        return std::nullopt;
      }
    Coord currCoord = battleMap.getCombatantCoordinates(*_factory._combatant).getRoot();
    if(_factory._combatant == &_target)
      {
        return CoordVector{currCoord};
      }
    if(!_factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(_target).get(), distances, _factory._combatant->getSize(),
                                                       LayOnHandsFactory::range, _factory._combatant->_instanceId);
      }
    if(battleMap.getCartesianDistanceCombatants(*_factory._combatant, _target) <= LayOnHandsFactory::range)
      {
        return CoordVector{currCoord};
      }
    return std::nullopt;
  }
}
