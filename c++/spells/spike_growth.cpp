#include "spells/spike_growth.hpp"
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/teams.hpp"
#include "core/conditions.hpp"
#include "core/geometry.hpp"
#include <memory>

namespace enc
{

  SpikeGrowthFactory::SpikeGrowthFactory(AbilityType abilityType, const std::shared_ptr<Combatant> &caster, Resource *resource)
      : DirectThreatFactory("SpikeGrowthFactory", "Spike Growth", caster, abilityType), _abilityType(abilityType), _resource(resource),
        _dmgDice({2, 4})
  {}

  Coord SpikeGrowthFactory::findBestArgs() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    auto [coord, maxScore, affectedCombatants] = battleMap.findBestPlacementHarmfulCircular(
      *_combatant.lock(), static_cast<int>(SpikeGrowthFactory::range), TRANSLATE_RADIUS.at(SpikeGrowthFactory::target));
    return coord;
  }

  std::vector<std::shared_ptr<Actoid>> SpikeGrowthFactory::createAll(void *previousActionInDag)
  {
    auto bestCoord = findBestArgs();
    return {std::make_unique<SpikeGrowth>(bestCoord, *this)};
  }

  std::shared_ptr<Actoid> SpikeGrowthFactory::create(void *target)
  {
    Coord *coord = static_cast<Coord *>(target);
    return std::make_shared<SpikeGrowth>(*coord, *this);
  }

  double SpikeGrowthFactory::calculateThreatToTarget(const Combatant &target, const Kwargs &kwargs) const { return avgRoll(_dmgDice); }

  double SpikeGrowthFactory::calculateThreatToTargetDelta(const Combatant &target, const ThreatModifiers &modifiers) const
  {
    return 0.0; // No need
  }

  double SpikeGrowthFactory::calculateMaxThreat() const
  {
    auto bestCoord = findBestArgs();
    return SpikeGrowth(bestCoord, *this).calculateThreat(Kwargs());
  }

  std::string SpikeGrowth::toString() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_SPIKE_GROWTH) ? "Quickened " : "";
    return prefix + "Spike Growth at (" + std::to_string(_coord[0]) + ", " + std::to_string(_coord[1]) + ")";
  }

  std::string SpikeGrowth::shorthandStr() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_SPIKE_GROWTH) ? "Quickened " : "";
    return prefix + "Spike Growth";
  }

  double SpikeGrowth::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    auto combatant = _factory._combatant.lock();

    std::vector<std::weak_ptr<Combatant>> affectedCombatants
      = battleMap.getCombatantsAffectedBySphereAoE(*combatant, SpikeGrowthFactory::target, SpellType::HARMFUL, _coord);

    double acc = 0.0;
    for(auto weakAffectedCombatant : affectedCombatants)
      {
        if(auto aff = weakAffectedCombatant.lock())
          {
            double avgDmg = avgRoll(_factory._dmgDice);
            acc += (teams.areEnemies(*combatant, *aff) ? 1.0 : -3.0) * avgDmg;
          }
      }
    return acc;
  }

  double SpikeGrowth::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return 0.0; // As per Python implementation
  }

  std::optional<CoordVector>
  SpikeGrowth::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    auto combatant = _factory._combatant.lock();
    if(combatant->getSwallowerPtr())
      {
        return std::nullopt;
      }

    BattleMap &battleMap = BattleMap::getInstance();
    if(!combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(Coords(_coord), distances, combatant->getSize(), static_cast<int>(SpikeGrowthFactory::range),
                                                       combatant->_instanceId);
      }
    else if(getCartesianDistanceCoords(battleMap.getCombatantCoordinates(*combatant), Coords(_coord)) <= static_cast<int>(SpikeGrowthFactory::range))
      {
        return CoordVector{battleMap.getCombatantCoordinates(*combatant).getRoot()};
      }

    return std::nullopt;
  }

  void SpikeGrowth::activate(const Kwargs &kwargs)
  {
    _factory._combatant.lock()->setConcentrationEffect(Effect::shared_from_this());
  }

  void SpikeGrowth::deactivate() { _factory._combatant.lock()->breakConcentration(); }
  bool SpikeGrowth::deactivateForCombatant(Combatant &combatant) {
    assert(false);
  }

  void SpikeGrowth::onEnter(Combatant &combatant)
  {
    int damage = rollDice(_factory._dmgDice);
    combatant.receiveDmg(damage, SpikeGrowthFactory::dmgType);
    BattleMap::getInstance().removeCombatantIfDead(combatant);
  }

  void SpikeGrowth::onMoveWithin(Combatant &combatant)
  {
    int damage = rollDice(_factory._dmgDice);
    combatant.receiveDmg(damage, SpikeGrowthFactory::dmgType);
    BattleMap::getInstance().removeCombatantIfDead(combatant);
  }

  void SpikeGrowth::onExit(Combatant &combatant) { /*NOP*/ };
  void SpikeGrowth::onStartOfTurn(Combatant &combatant) { /*NOP */ };
  void SpikeGrowth::onEndOfTurn(Combatant &combatant) { /*NOP*/ };

  double SpikeGrowth::threatOnEnter(const Combatant &target, const Kwargs &kwargs) const { return avgRoll(_factory._dmgDice); }

  double SpikeGrowth::threatOnMoveWithin(const Combatant &target, const Kwargs &kwargs) const { return avgRoll(_factory._dmgDice); }

  size_t SpikeGrowth::hash() const
  {
    size_t h = std::hash<int>{}(static_cast<int>(getAbilityType()));
    h ^= std::hash<int>{}(static_cast<int>(getFlags())) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_coord[0]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_coord[1]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    return h;
  }

  bool SpikeGrowth::equals(const Actoid &other) const
  {
    if(auto *spikeGrowth = dynamic_cast<const SpikeGrowth *>(&other))
      {
        return getAbilityType() == other.getAbilityType() && getFlags() == other.getFlags() && _coord == spikeGrowth->_coord;
      }
    return false;
  }

} // namespace enc
