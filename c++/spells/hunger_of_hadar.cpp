// hunger_of_hadar.cpp
#include "spells/hunger_of_hadar.hpp"
#include "core/battle_map.hpp"
#include "core/teams.hpp"
#include "core/combatant.hpp"
#include "effects/effect_tracker.hpp"
#include "effects/aoe_effect.hpp"
#include "core/conditions.hpp"
#include "core/action_resolver.hpp"
#include "core/geometry.hpp"

namespace enc
{
  HungerOfHadarFactory::HungerOfHadarFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("HungerOfHadarFactory", "Hunger of Hadar", caster, abilityType), _dc(dc), _abilityType(abilityType), _resource(resource),
        _savingThrow(SavingThrow::DEX), _dmgDice({{2, 6}})
  {
    setFlag(FactoryFlags::DEX_SAVE_APPLIES);
  }

  std::vector<std::shared_ptr<Actoid>> HungerOfHadarFactory::createAll(void *previousActionInDag)
  {
    auto &battleMap = BattleMap::getInstance();
    auto [coord, _1, _2] = battleMap.findBestPlacementHarmfulCircular(_combatant, static_cast<int>(HungerOfHadarFactory::range),
                                                                    TRANSLATE_RADIUS.at(HungerOfHadarFactory::target));
    return {std::make_shared<HungerOfHadar>(coord, *this)};
  }

  std::shared_ptr<Actoid> HungerOfHadarFactory::create(void *target) { return std::make_shared<HungerOfHadar>(*static_cast<Coord *>(target), *this); }

  double HungerOfHadarFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    // The 0.5 is a heuristic expressing that most targets would leave the area
    auto avgDmg = std::min(static_cast<double>(target->getCurrentHp()),
                           meanDmgDcAttack(_dc, {_dmgDice}, false, target->getSavingThrow(_savingThrow), target->isImmuneTo(DamageType::Acid),
                                           target->isResistantTo(DamageType::Acid)));

    return avgRoll(_dmgDice) + 0.5 * avgDmg;
  }

  double HungerOfHadarFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    return 0.0; // No need
  }

  double HungerOfHadarFactory::calculateMaxThreat() const
  {
    auto &battleMap = BattleMap::getInstance();
    auto [coord, _1, _2] = battleMap.findBestPlacementHarmfulCircular(_combatant, static_cast<int>(HungerOfHadarFactory::range),
                                                                    TRANSLATE_RADIUS.at(HungerOfHadarFactory::target));
    HungerOfHadar effect(coord, *this);
    return effect.calculateThreat({});
  }

  HungerOfHadar::HungerOfHadar(const Coord &coord, const HungerOfHadarFactory &factory)
      : Effect(factory._combatant), AoeEffect(factory._combatant),
        Actoid(const_cast<HungerOfHadarFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
        LimitedDurationEffect(factory._combatant, 10), AoeSphericEffect(factory._combatant, coord, TRANSLATE_RADIUS.at(HungerOfHadarFactory::target)),
        _coord(coord), _factory(factory)
  {}

  void HungerOfHadar::onStartOfTurn(Combatant *combatant)
  {
    combatant->applyCondition(std::make_shared<Condition>(Conditions::BLINDED, _factory._combatant, this));
    int damage = rollDice(_factory._dmgDice);
    combatant->receiveDmg(damage, _factory.dmgType);
    BattleMap::getInstance().removeCombatantIfDead(*combatant);
  }

  void HungerOfHadar::onEndOfTurn(Combatant *combatant)
  {
    combatant->applyCondition(std::make_shared<Condition>(Conditions::BLINDED, _factory._combatant, this));
    int damage = rollDice(_factory._dmgDice);

    // Temporarily change damage type for acid damage
    auto originalDmgType = _factory.dmgType;
    resolveDmgSavingThrow(_factory._savingThrow, _factory._dc, shorthandStr(), damage, DamageType::Acid, combatant, false, true);
  }

  void HungerOfHadar::onEnter(Combatant *combatant)
  {
    combatant->applyCondition(std::make_shared<Condition>(Conditions::BLINDED, _factory._combatant, this));
  }

  void HungerOfHadar::onMoveWithin(Combatant *combatant)
  {
    // No effect when moving within area
  }

  void HungerOfHadar::onExit(Combatant *combatant) { combatant->removeCondition(Conditions::BLINDED, _factory._combatant); }

  void HungerOfHadar::activate(const Kwargs &kwargs)
  {
    auto &effectTracker = EffectTracker::getInstance();
    effectTracker.add(Effect::shared_from_this());
    _factory._combatant->setConcentrationEffect(Effect::shared_from_this());
    // TODO: Make area difficult terrain
  }

  void HungerOfHadar::deactivate()
  {
    _factory._combatant->breakConcentration();
    // TODO: Remove difficult terrain
  }

  bool HungerOfHadar::deactivateForCombatant(Combatant *combatant) { throw std::runtime_error("Not implemented"); }

  double HungerOfHadar::calculateThreat(const Kwargs &kwargs)
  {
    auto &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    auto affected = battleMap.getCombatantsAffectedBySphereAoE(_factory._combatant, HungerOfHadarFactory::target, HungerOfHadarFactory::type, _coord);

    double totalThreat = 0.0;
    for(auto *target : affected)
      {
        // Initial cold damage
        totalThreat += avgRoll(_factory._dmgDice);

        // Potential acid damage with 0.5 multiplier (assuming targets try to leave)
        double avgDmg = std::min(static_cast<double>(target->getCurrentHp()),
                                 meanDmgDcAttack(_factory._dc, {_factory._dmgDice}, false, target->getSavingThrow(_factory._savingThrow),
                                                 target->isImmuneTo(DamageType::Acid), target->isResistantTo(DamageType::Acid)));
        totalThreat += 0.5 * avgDmg;

        // Adjust for friendly fire
        totalThreat *= (teams.areEnemies(*_factory._combatant, *target) ? 1.0 : -3.0);
      }
    return totalThreat;
  }

  double HungerOfHadar::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return 0.0; // Not relevant for this ability
  }

  std::string HungerOfHadar::toString() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_HUNGER_OF_HADAR) ? "Quickened " : "";
    std::stringstream ss;
    ss << _coord;
    return prefix + "Hunger of Hadar at " + ss.str();
  }

  std::string HungerOfHadar::shorthandStr() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_HUNGER_OF_HADAR) ? "Quickened " : "";
    return prefix + "Hunger of Hadar";
  }

  EffectType HungerOfHadar::getEffectType() const { return EffectType::HUNGER_OF_HADAR; }

  const CoordVector &HungerOfHadar::getAffectedCoords() const { return SphericAoe::getAffectedCoords(); }

  std::optional<CoordVector>
  HungerOfHadar::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    if(_factory._combatant->getSwallower())
      {
        return std::nullopt;
      }

    auto &battleMap = BattleMap::getInstance();

    if(!_factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(Coords(_origin), distances, _factory._combatant->getSize(),
                                                       static_cast<int>(HungerOfHadarFactory::range), _factory._combatant->_instanceId);
      }

    const Coords &combatantPos = battleMap.getCombatantCoordinates(*_factory._combatant);
    if(getCartesianDistanceCoords(combatantPos, _origin) <= static_cast<double>(HungerOfHadarFactory::range))
      {
        return CoordVector{combatantPos.getRoot()};
      }

    return std::nullopt;
  }

  size_t HungerOfHadar::hash() const
  {
    size_t h = std::hash<int>{}(static_cast<int>(getAbilityType()));
    h ^= std::hash<int>{}(static_cast<int>(getFlags())) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_coord[0]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_coord[1]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    return h;
  }

  bool HungerOfHadar::equals(const Actoid &other) const
  {
    if(auto *hungerOfHadar = dynamic_cast<const HungerOfHadar *>(&other))
      {
        return getAbilityType() == other.getAbilityType() && getFlags() == other.getFlags() && _coord == hungerOfHadar->_coord;
      }
    return false;
  }
}
