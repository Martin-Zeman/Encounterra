#include "spells/sleep.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include "core/teams.hpp"
#include "core/threat_utils.hpp"
#include "core/geometry.hpp"
#include <algorithm>
#include <iostream>

namespace enc
{
  namespace
  {
    constexpr int ROUND_HORIZON = 2;
    constexpr int MELEE_THREAT_RADIUS = 6;
  }

  SleepFactory::SleepFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("SleepFactory", "Sleep", caster, abilityType), _dc(dc), _resource(resource)
  {
    setFlag(FactoryFlags::PREVENT_ENDLESS_RECURSION);
  }

  Coord SleepFactory::findBestArgs() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    auto [coord, ignoredScore, ignoredAffected]
        = battleMap.findBestPlacementHarmfulCircular(_combatant, static_cast<int>(SleepFactory::range), TRANSLATE_RADIUS.at(SleepFactory::target));
    return coord;
  }

  std::vector<std::shared_ptr<Actoid>> SleepFactory::createAll(void *previousActionInDag)
  {
    if(_combatant->getSwallower())
      {
        return {};
      }
    return {std::make_shared<Sleep>(findBestArgs(), *this)};
  }

  std::shared_ptr<Actoid> SleepFactory::create(void *target)
  {
    return std::make_shared<Sleep>(*static_cast<Coord *>(target), *this);
  }

  double SleepFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(target->isAffectedByAny({Conditions::INCAPACITATED, Conditions::UNCONSCIOUS, Conditions::STUNNED, Conditions::PARALYZED})
       || target->isImmuneToCondition(Conditions::INCAPACITATED) || target->isImmuneToCondition(Conditions::UNCONSCIOUS)
       || battleMap.getCartesianDistanceCombatants(*_combatant, *target)
              > static_cast<double>(static_cast<int>(SleepFactory::range) + TRANSLATE_RADIUS.at(SleepFactory::target)))
      {
        return 0.0;
      }

    Teams &teams = Teams::getInstance();
    double maxActionThreat = 0.0;
    auto enemies = teams.getAliveNonSwallowedEnemies(*target);
    auto accumulateBest = [&](const std::vector<std::shared_ptr<ActoidFactory>> &factories) {
      for(const auto &factory : factories)
        {
          auto threatFactory = std::dynamic_pointer_cast<DirectThreatFactory>(factory);
          if(!threatFactory || threatFactory->hasFlag(FactoryFlags::PREVENT_ENDLESS_RECURSION))
            {
              continue;
            }
          for(auto *enemy : enemies)
            {
              maxActionThreat = std::max(maxActionThreat, threatFactory->calculateThreatToTarget(enemy, {}));
            }
        }
    };
    accumulateBest(target->getActionFactoriesConst());
    accumulateBest(target->getBonusActionFactoriesConst());

    ThreatModifiers unconsciousMods;
    unconsciousMods.set(ThreatModifierType::ROLL_TYPE, RollType::ADVANTAGE);
    unconsciousMods.set(ThreatModifierType::AUTO_CRIT, true);
    double threatInDelta = std::min(static_cast<double>(target->getCurrentHp()),
                                    calculateThreatInDelta(target, MELEE_THREAT_RADIUS, unconsciousMods,
                                                           static_cast<uint32_t>(FactoryFlags::IS_ATTACK_LIKE))
                                        .second);

    double pFail = getSavingThrowFailProb(_dc, target->getSavingThrow(SleepFactory::savingThrow));
    return pFail * maxActionThreat + pFail * pFail * threatInDelta * ROUND_HORIZON;
  }

  double SleepFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const { return 0.0; }

  double SleepFactory::calculateMaxThreat() const { return Sleep(findBestArgs(), *this).calculateThreat({}); }

  std::string Sleep::toString() const
  {
    return "Sleep at (" + std::to_string(_coord[0]) + ", " + std::to_string(_coord[1]) + ")";
  }

  std::string Sleep::shorthandStr() const { return "Sleep"; }

  bool Sleep::canAffect(Combatant *target) const
  {
    return target->isAlive() && !target->isAffectedByAny({Conditions::INCAPACITATED, Conditions::UNCONSCIOUS, Conditions::STUNNED, Conditions::PARALYZED})
           && !target->isImmuneToCondition(Conditions::INCAPACITATED) && !target->isImmuneToCondition(Conditions::UNCONSCIOUS);
  }

  double Sleep::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    std::vector<Combatant *> affected = battleMap.getCombatantsAffectedBySphereAoE(_factory._combatant, SleepFactory::target, SleepFactory::type, _coord);
    double threat = 0.0;
    for(auto *target : affected)
      {
        if(canAffect(target))
          {
            threat += (teams.areEnemies(*_factory._combatant, *target) ? 1.0 : -4.0) * _factory.calculateThreatToTarget(target, {});
          }
      }
    return threat;
  }

  double Sleep::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0.0; }

  void Sleep::activate(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    std::vector<Combatant *> affected = battleMap.getCombatantsAffectedBySphereAoE(_factory._combatant, SleepFactory::target, SleepFactory::type, _coord);
    for(auto *target : affected)
      {
        if(!teams.areEnemies(*_factory._combatant, *target) || !canAffect(target))
          {
            continue;
          }
        bool saved = rollSavingThrow(target->getSavingThrow(SleepFactory::savingThrow), _factory._dc,
                                     reconcileRollTypes(target->getSavingThrowRollTypeMods(SleepFactory::savingThrow)));
        if(!saved)
          {
            target->applyCondition(Condition(Conditions::INCAPACITATED | Conditions::AWAKENED_BY_DMG | Conditions::CAN_BE_SHAKEN_AWAKE,
                                             _factory._combatant, this));
            _combatants.push_back(target);
            _awaitingSecondSave.insert(target);
            std::cout << target->_name << " is Incapacitated by Sleep" << std::endl;
          }
      }
    if(!_combatants.empty())
      {
        _factory._combatant->setConcentrationEffect(Effect::shared_from_this());
      }
  }

  void Sleep::removeSleepConditions(Combatant *target) const
  {
    target->removeCondition(Conditions::INCAPACITATED, _factory._combatant);
    target->removeCondition(Conditions::UNCONSCIOUS, _factory._combatant);
    target->removeCondition(Conditions::AWAKENED_BY_DMG, _factory._combatant);
    target->removeCondition(Conditions::CAN_BE_SHAKEN_AWAKE, _factory._combatant);
  }

  void Sleep::deactivate()
  {
    for(auto *target : _combatants)
      {
        removeSleepConditions(target);
      }
    _combatants.clear();
    _awaitingSecondSave.clear();
    _factory._combatant->breakConcentration();
  }

  bool Sleep::deactivateForCombatant(Combatant *combatant)
  {
    removeSleepConditions(combatant);
    _awaitingSecondSave.erase(combatant);
    _combatants.erase(std::remove(_combatants.begin(), _combatants.end(), combatant), _combatants.end());
    if(_combatants.empty())
      {
        _factory._combatant->breakConcentration();
        return false;
      }
    return true;
  }

  bool Sleep::combatantSavedAtEndOfTurn(Combatant *combatant)
  {
    if(!_awaitingSecondSave.contains(combatant))
      {
        return true;
      }
    bool saved = rollSavingThrow(combatant->getSavingThrow(SleepFactory::savingThrow), _factory._dc,
                                 reconcileRollTypes(combatant->getSavingThrowRollTypeMods(SleepFactory::savingThrow)));
    if(saved)
      {
        std::cout << combatant->_name << " shakes off Sleep" << std::endl;
        return false;
      }

    combatant->removeCondition(Conditions::INCAPACITATED, _factory._combatant);
    combatant->applyCondition(Condition(Conditions::UNCONSCIOUS | Conditions::INCAPACITATED | Conditions::AWAKENED_BY_DMG
                                          | Conditions::CAN_BE_SHAKEN_AWAKE,
                                        _factory._combatant, this));
    _awaitingSecondSave.erase(combatant);
    std::cout << combatant->_name << " falls Unconscious from Sleep" << std::endl;
    return true;
  }

  std::optional<CoordVector>
  Sleep::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    Combatant *caster = _factory._combatant;
    if(caster->getSwallower())
      {
        return std::nullopt;
      }
    BattleMap &battleMap = BattleMap::getInstance();
    Coord currCoord = battleMap.getCombatantCoordinates(*caster).getRoot();
    if(!caster->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(Coords(_coord), distances, caster->getSize(), static_cast<int>(SleepFactory::range),
                                                       caster->_instanceId);
      }
    if(getCartesianDistanceCoords(battleMap.getCombatantCoordinates(*caster), Coords(_coord)) <= static_cast<int>(SleepFactory::range))
      {
        return CoordVector{currCoord};
      }
    return std::nullopt;
  }
}
