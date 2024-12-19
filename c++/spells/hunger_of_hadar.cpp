// hunger_of_hadar.cpp
#include "spells/hunger_of_hadar.hpp"
#include "core/battle_map.hpp"
#include "core/teams.hpp"
#include "core/combatant.hpp"
#include "effects/effect_tracker.hpp"
#include "effects/aoe_effect.hpp"
#include "core/conditions.hpp"

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
    auto coord = battleMap.findBestPlacementHarmfulCircular(_combatant, static_cast<int>(HungerOfHadarFactory::range), TRANSLATE_RADIUS.at(HungerOfHadarFactory::target));

    if(!coord.empty())
      {
        return {std::make_shared<HungerOfHadar>(coord, *this)};
      }
    return {};
  }

  std::shared_ptr<Actoid> HungerOfHadarFactory::create(void *target) { return std::make_shared<HungerOfHadar>(*static_cast<Coord *>(target), *this); }

  double HungerOfHadarFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    // The 0.5 is a heuristic expressing that most targets would leave the area
    auto avgDmg
      = std::min(static_cast<double>(target->getCurrentHp()), meanDmgDcAttack(_dc, {_dmgDice}, false, target->getSavingThrow(_savingThrow),
                                                                  target->isImmuneTo(DamageType::Acid), target->isResistantTo(DamageType::Acid)));

    return avgRoll(_dmgDice) + 0.5 * avgDmg;
  }

  double HungerOfHadarFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    return 0.0; // No need
  }

  double HungerOfHadarFactory::calculateMaxThreat() const
  {
    auto &battleMap = BattleMap::getInstance();
    auto coord = battleMap.findBestPlacementHarmfulCircular(_combatant, static_cast<int>(HungerOfHadarFactory::range), TRANSLATE_RADIUS.at(HungerOfHadarFactory::target));

    if(!coord.empty())
      {
        HungerOfHadar effect(coord, *this);
        return effect.calculateThreat();
      }
    return 0.0;
  }

  HungerOfHadar::HungerOfHadar(const Coord &coord, const HungerOfHadarFactory &factory)
      : Effect(factory._combatant), AoeEffect(factory._combatant),
        Actoid(const_cast<HungerOfHadarFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
        LimitedDurationEffect(factory._combatant, 10), AoeSphericEffect(factory._combatant, coord, TRANSLATE_RADIUS.at(HungerOfHadarFactory::target)),
        _coord(coord), _factory(factory)
  {}

  void HungerOfHadar::onStartOfTurn(Combatant *combatant)
  {
    applyCondition(combatant, Condition(Conditions::BLINDED, _factory._combatant, this));
    int damage = rollDice(_factory._dmgDice);
    combatant->receiveDamage(damage, _factory.dmgType);
    Map::getInstance().removeCombatantIfDead(combatant);
  }

  void HungerOfHadar::onEndOfTurn(Combatant *combatant)
  {
    applyCondition(combatant, Condition(Conditions::BLINDED, _factory._combatant, this));
    int damage = rollDice(_factory._dmgDice);

    // Temporarily change damage type for acid damage
    auto originalDmgType = _factory.dmgType;
    const_cast<HungerOfHadarFactory &>(_factory).dmgType = DamageType::Acid;
    resolveDamageSavingThrow(this, damage, combatant, false, true);
    const_cast<HungerOfHadarFactory &>(_factory).dmgType = originalDmgType;
  }

  void HungerOfHadar::onEnter(Combatant *combatant) { applyCondition(combatant, Condition(Conditions::BLINDED, _factory._combatant, this)); }

  void HungerOfHadar::onMoveWithin(Combatant *combatant)
  {
    // No effect when moving within area
  }

  void HungerOfHadar::onExit(Combatant *combatant) { removeCondition(combatant, Conditions::BLINDED, _factory._combatant); }

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

  void HungerOfHadar::deactivateForCombatant(Combatant *combatant) { throw std::runtime_error("Not implemented"); }

  double HungerOfHadar::calculateThreat(const Kwargs &kwargs)
  {
    auto &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    auto affected = battleMap.getCombatantsAffectedBySphereAoe(_factory._combatant, HungerOfHadarFactory::target, HungerOfHadarFactory::type, _coord);

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
        totalThreat *= (teams.areEnemies(*_factory._combatant, target) ? 1.0 : -3.0);
      }
    return totalThreat;
  }

  double HungerOfHadar::calculateThreatDelta(const ThreatModifiers &modifiers)
  {
    return 0.0; // Not relevant for this ability
  }

  std::string HungerOfHadar::toString() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_HUNGER_OF_HADAR) ? "Quickened " : "";
    return prefix + "Hunger Of Hadar at " + _coord.toString();
  }

  std::string HungerOfHadar::shorthandStr() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_HUNGER_OF_HADAR) ? "Quickened " : "";
    return prefix + "Hunger Of Hadar";
  }

  EffectType HungerOfHadar::getEffectType() const { return EffectType::HUNGER_OF_HADAR; }
}
