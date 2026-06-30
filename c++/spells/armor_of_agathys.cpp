#include "spells/armor_of_agathys.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include "effects/effect_tracker.hpp"

namespace enc
{
  ArmorOfAgathysFactory::ArmorOfAgathysFactory(AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("ArmorOfAgathysFactory", "Armor of Agathys", caster, abilityType), _resource(resource)
  {}

  std::vector<std::shared_ptr<Actoid>> ArmorOfAgathysFactory::createAll(void *previousActionInDag)
  {
    return {std::make_shared<ArmorOfAgathys>(*this)};
  }

  std::shared_ptr<Actoid> ArmorOfAgathysFactory::create(void *target) { return std::make_shared<ArmorOfAgathys>(*this); }

  int ArmorOfAgathysFactory::getScaledValue() const
  {
    // Base 5 at level 1, +5 for each slot level above 1 (i.e. 5 x cast level). Warlocks upcast to their pact
    // slot level via getCastingSlotLevel.
    return ArmorOfAgathysFactory::TEMP_HP * _combatant->getCastingSlotLevel(ArmorOfAgathysFactory::level);
  }

  double ArmorOfAgathysFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    // The buff is purely defensive: it soaks temporary Hit Points of damage and punishes melee attackers with
    // Cold damage. Approximate its value as the temporary Hit Points plus the retaliation against each adjacent
    // enemy, both scaled to the (upcast) slot level it is cast at.
    auto &battleMap = BattleMap::getInstance();
    int adjacentEnemies = static_cast<int>(battleMap.getNonSwallowedEnemiesWithinHopDistance(_combatant, 1).size());
    int scaledValue = getScaledValue();
    return scaledValue + scaledValue * adjacentEnemies;
  }

  double ArmorOfAgathysFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const { return 0.0; }

  double ArmorOfAgathysFactory::calculateMaxThreat() const { return calculateThreatToTarget(_combatant, {}); }

  std::string ArmorOfAgathys::toString() const { return "Armor of Agathys"; }

  std::string ArmorOfAgathys::shorthandStr() const { return "Armor of Agathys"; }

  double ArmorOfAgathys::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(_factory._combatant, kwargs); }

  double ArmorOfAgathys::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0.0; }

  void ArmorOfAgathys::activate(const Kwargs &kwargs)
  {
    EffectTracker::getInstance().add(Effect::shared_from_this());
    int scaledValue = _factory.getScaledValue();
    _retaliationDamage = scaledValue;
    _factory._combatant->setTemporaryHp(scaledValue);
    std::cout << _factory._combatant->_name << " gains " << scaledValue << " temporary hit points from Armor of Agathys"
              << std::endl;
  }

  void ArmorOfAgathys::deactivate() { /* The temporary Hit Points fade on their own; nothing to undo. */ }

  bool ArmorOfAgathys::deactivateForCombatant(Combatant *combatant) { return false; }

  std::optional<CoordVector>
  ArmorOfAgathys::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
  }
}
