#include "spells/mage_armor.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include "core/threat_utils.hpp"
#include <algorithm>

namespace enc
{
  namespace
  {
    constexpr int INCOMING_ATTACK_THREAT_RADIUS = 6;
  }

  MageArmorFactory::MageArmorFactory(Combatant *caster, Resource *resource, int armoredBaseAc)
      : ThreatModifierFactory("MageArmorFactory", "Mage Armor", caster, AbilityType::MAGE_ARMOR), _resource(resource), _armoredBaseAc(armoredBaseAc)
  {}

  std::vector<Combatant *> MageArmorFactory::getEligibleTargets() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    std::vector<Combatant *> targets = battleMap.getNonSwallowedAlliesWithinRadius(_combatant, static_cast<int>(MageArmorFactory::range));
    targets.push_back(_combatant);
    targets.erase(std::remove_if(targets.begin(), targets.end(), [&](Combatant *target) {
                    return target->getSwallower() || target->getAC() >= _armoredBaseAc;
                  }),
                  targets.end());
    return targets;
  }

  std::vector<std::shared_ptr<Actoid>> MageArmorFactory::createAll(void *previousActionInDag)
  {
    auto targets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(targets.size());
    for(auto *target : targets)
      {
        result.push_back(std::make_shared<MageArmor>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> MageArmorFactory::create(void *target)
  {
    return std::make_shared<MageArmor>(*static_cast<Combatant *>(target), *this);
  }

  double MageArmorFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(target->getSwallower() || battleMap.getCartesianDistanceCombatants(*_combatant, *target) > static_cast<int>(MageArmorFactory::range))
      {
        return 0.0;
      }
    int acDelta = std::max(0, _armoredBaseAc - target->getAC());
    if(acDelta == 0)
      {
        return 0.0;
      }

    ThreatModifiers modifiers;
    modifiers.set(ThreatModifierType::TARGET_AC, acDelta);
    return std::max(0.0, -calculateThreatInDelta(target, INCOMING_ATTACK_THREAT_RADIUS, modifiers,
                                                 static_cast<uint32_t>(FactoryFlags::IS_ATTACK_LIKE))
                            .first);
  }

  double MageArmorFactory::calculateMaxThreat() const
  {
    double maxThreat = 0.0;
    for(auto *target : getEligibleTargets())
      {
        maxThreat = std::max(maxThreat, calculateThreatToTarget(target, {}));
      }
    return maxThreat;
  }

  std::string MageArmor::toString() const { return "Mage Armor on " + _target._name; }

  std::string MageArmor::shorthandStr() const { return "Mage Armor"; }

  double MageArmor::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(&_target, kwargs); }

  double MageArmor::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0.0; }

  void MageArmor::activate(const Kwargs &kwargs)
  {
    _appliedAcDelta = std::max(0, _factory._armoredBaseAc - _target.getAC());
    if(_appliedAcDelta > 0)
      {
        _target.setAC(_target.getAC() + _appliedAcDelta);
      }
  }

  void MageArmor::deactivate()
  {
    if(_appliedAcDelta > 0)
      {
        _target.setAC(_target.getAC() - _appliedAcDelta);
        _appliedAcDelta = 0;
      }
  }

  bool MageArmor::deactivateForCombatant(Combatant *combatant)
  {
    if(combatant == &_target)
      {
        deactivate();
      }
    return false;
  }

  std::optional<CoordVector>
  MageArmor::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *caster = _factory._combatant;
    if(caster->getSwallower())
      {
        return std::nullopt;
      }
    Coord currCoord = battleMap.getCombatantCoordinates(*caster).getRoot();
    if(!caster->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(_target).get(), distances, caster->getSize(),
                                                       static_cast<int>(MageArmorFactory::range), caster->_instanceId);
      }
    if(battleMap.getCartesianDistanceCombatants(*caster, _target) <= static_cast<int>(MageArmorFactory::range))
      {
        return CoordVector{currCoord};
      }
    return std::nullopt;
  }
}
