#include "spells/shield_of_faith.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/threat_utils.hpp"
#include <algorithm>

namespace enc
{
  ShieldOfFaithFactory::ShieldOfFaithFactory(Combatant *caster, Resource *resource)
      : ThreatModifierFactory("ShieldOfFaithFactory", "Shield of Faith", caster, AbilityType::SHIELD_OF_FAITH), _resource(resource)
  {}

  std::vector<Combatant *> ShieldOfFaithFactory::getEligibleTargets() const
  {
    std::vector<Combatant *> targets;
    if(_combatant->getSwallower())
      {
        targets.push_back(_combatant);
        return targets;
      }
    targets = BattleMap::getInstance().getNonSwallowedAlliesWithinRadius(_combatant, static_cast<int>(ShieldOfFaithFactory::range));
    targets.push_back(_combatant);
    return targets;
  }

  std::vector<std::shared_ptr<Actoid>> ShieldOfFaithFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    for(auto *target : getEligibleTargets())
      {
        result.push_back(std::make_shared<ShieldOfFaith>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> ShieldOfFaithFactory::create(void *target)
  {
    return std::make_shared<ShieldOfFaith>(*static_cast<Combatant *>(target), *this);
  }

  double ShieldOfFaithFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    ThreatModifiers mods;
    mods.set(ThreatModifierType::TARGET_AC, ShieldOfFaithFactory::acBonus);
    auto [minDelta, maxDelta] = calculateThreatInDelta(target, 12, mods, static_cast<uint32_t>(FactoryFlags::IS_ATTACK_LIKE));
    return std::max(0.0, -minDelta);
  }

  ShieldOfFaith::ShieldOfFaith(Combatant &target, ShieldOfFaithFactory &factory)
      : Effect(factory.getCombatant(), &target), Actoid(factory, ActoidFlags::IS_SPELL, AbilityType::SHIELD_OF_FAITH),
        CombatantEffect(factory.getCombatant(), {&target}), LimitedDurationEffect(factory.getCombatant(), 100), _factory(factory)
  {}

  void ShieldOfFaith::activate(const Kwargs &kwargs)
  {
    if(!_applied)
      {
        getCombatants().front()->setAC(getCombatants().front()->getAC() + ShieldOfFaithFactory::acBonus);
        _applied = true;
      }
    _factory.getCombatant()->setConcentrationEffect(std::dynamic_pointer_cast<Effect>(shared_from_this()));
  }

  void ShieldOfFaith::deactivate()
  {
    if(_applied)
      {
        getCombatants().front()->setAC(getCombatants().front()->getAC() - ShieldOfFaithFactory::acBonus);
        _applied = false;
      }
    _factory.getCombatant()->breakConcentration();
  }

  bool ShieldOfFaith::deactivateForCombatant(Combatant *combatant)
  {
    deactivate();
    return false;
  }

  std::string ShieldOfFaith::toString() const { return "Shield of Faith on " + getCombatants().front()->_name; }

  std::string ShieldOfFaith::shorthandStr() const { return "Shield of Faith"; }

  double ShieldOfFaith::calculateThreat(const Kwargs &kwargs)
  {
    return _factory.calculateThreatToTarget(getCombatants().front(), kwargs);
  }

  std::optional<CoordVector> ShieldOfFaith::getEligibleCoords(const blaze::DynamicVector<int> &distances,
                                                              const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *caster = _factory.getCombatant();
    Combatant *target = getCombatants().front();
    Coord currCoord = battleMap.getCombatantCoordinates(*caster).getRoot();
    if(caster->getSwallower())
      {
        return CoordVector{currCoord};
      }
    if(!caster->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(*target).get(), distances, caster->getSize(),
                                                       static_cast<int>(ShieldOfFaithFactory::range), caster->_instanceId);
      }
    if(battleMap.getCartesianDistanceCombatants(*caster, *target) <= static_cast<int>(ShieldOfFaithFactory::range))
      {
        return CoordVector{currCoord};
      }
    return CoordVector{};
  }
}
