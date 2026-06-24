#include "spells/hold_person.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include "core/teams.hpp"
#include "core/threat_utils.hpp"
#include "core/conditions.hpp"
#include "core/geometry.hpp"
#include <memory>
#include <limits>
#include <algorithm>

namespace enc
{

  namespace
  {
    // Number of future rounds over which Hold Person's prevented/enabled threat is projected.
    constexpr int ROUND_HORIZON = 3;
    constexpr int MELEE_THREAT_RADIUS = 6;
  }

  HoldPersonFactory::HoldPersonFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("HoldPersonFactory", "Hold Person", caster, abilityType), _dc(dc), _resource(resource)
  {
    setFlag(FactoryFlags::PREVENT_ENDLESS_RECURSION);
  }

  std::vector<Combatant *> HoldPersonFactory::getEligibleTargets() const
  {
    if(_combatant->getSwallower())
      {
        return {}; // Must be able to see the target
      }
    BattleMap &battleMap = BattleMap::getInstance();
    std::vector<Combatant *> result;
    for(auto *e : battleMap.getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(HoldPersonFactory::range)))
      {
        if(e->isHumanoid())
          {
            result.push_back(e);
          }
      }
    return result;
  }

  std::vector<std::shared_ptr<Actoid>> HoldPersonFactory::createAll(void *previousActionInDag)
  {
    auto targets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(targets.size());
    for(auto *t : targets)
      {
        result.push_back(std::make_shared<HoldPerson>(*t, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> HoldPersonFactory::create(void *target)
  {
    return std::make_shared<HoldPerson>(*static_cast<Combatant *>(target), *this);
  }

  double HoldPersonFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    return threatToTargetWithDc(target, _dc);
  }

  double HoldPersonFactory::threatToTargetWithDc(Combatant *target, int dc) const
  {
    if(target->isAffectedBy(Conditions::PARALYZED))
      {
        return 0;
      }
    BattleMap &battleMap = BattleMap::getInstance();
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target) > static_cast<int>(HoldPersonFactory::range))
      {
        return 0;
      }

    // Outgoing threat we deny the target by paralyzing it: the best single-target damage it could
    // otherwise deal with an action or bonus action. calculateMaxThreat() is protected on other
    // factories, so we evaluate the public per-target threat against the target's own enemies.
    Teams &teams = Teams::getInstance();
    auto targetsEnemies = teams.getAliveNonSwallowedEnemies(*target);
    double maxActionThreat = 0.0;
    auto accumulateBest = [&](const std::vector<std::shared_ptr<ActoidFactory>> &factories) {
      for(const auto &factory : factories)
        {
          auto threatFactory = std::dynamic_pointer_cast<DirectThreatFactory>(factory);
          if(!threatFactory || threatFactory->hasFlag(FactoryFlags::PREVENT_ENDLESS_RECURSION))
            {
              continue;
            }
          for(auto *enemy : targetsEnemies)
            {
              maxActionThreat = std::max(maxActionThreat, threatFactory->calculateThreatToTarget(enemy, {}));
            }
        }
    };
    accumulateBest(target->getActionFactoriesConst());
    accumulateBest(target->getBonusActionFactoriesConst());

    // Bonus our allies gain by attacking the paralyzed target (advantage + auto-crit in melee).
    ThreatModifiers mods;
    mods.set(ThreatModifierType::ROLL_TYPE, RollType::ADVANTAGE);
    mods.set(ThreatModifierType::AUTO_CRIT, true);
    double threatInDelta = std::min(static_cast<double>(target->getCurrentHp()),
                                    calculateThreatInDelta(target, MELEE_THREAT_RADIUS, mods,
                                                           static_cast<uint32_t>(FactoryFlags::IS_ATTACK_LIKE))
                                        .second);

    double threatRoundTotal = maxActionThreat + threatInDelta;

    double pFail = getSavingThrowFailProb(dc, target->getSavingThrow(HoldPersonFactory::savingThrow));
    double pFailAcc = pFail;
    double totalThreat = 0.0;
    for(int i = 0; i < ROUND_HORIZON; ++i)
      {
        totalThreat += threatRoundTotal * pFailAcc;
        pFailAcc *= pFail;
      }
    return totalThreat;
  }

  double HoldPersonFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    // Hold Person lands on a Wisdom save, so a flat bonus to the caster's spell save DC raises the chance
    // the target stays paralyzed. The delta is the extra threat the higher DC buys over the spell's horizon.
    int saveDcBonus = modifiers.getOrDefault(ThreatModifierType::SAVE_DC, 0);
    if(saveDcBonus == 0)
      {
        return 0;
      }
    return threatToTargetWithDc(target, _dc + saveDcBonus) - threatToTargetWithDc(target, _dc);
  }

  double HoldPersonFactory::calculateMaxThreat() const
  {
    auto targets = getEligibleTargets();
    double maxThreat = 0.0;
    for(auto *t : targets)
      {
        maxThreat = std::max(maxThreat, calculateThreatToTarget(t, {}));
      }
    return maxThreat;
  }

  std::string HoldPerson::toString() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_HOLD_PERSON) ? "Quickened " : "";
    return prefix + "Hold Person on " + getCombatants()[0]->_name;
  }

  std::string HoldPerson::shorthandStr() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_HOLD_PERSON) ? "Quickened " : "";
    return prefix + "Hold Person";
  }

  double HoldPerson::calculateThreat(const Kwargs &kwargs)
  {
    return _factory.calculateThreatToTarget(getCombatants()[0], kwargs);
  }

  double HoldPerson::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return _factory.calculateThreatToTargetDelta(getCombatants()[0], modifiers);
  }

  void HoldPerson::activate(const Kwargs &kwargs)
  {
    Combatant *target = getCombatants()[0];
    bool saved = rollSavingThrow(target->getSavingThrow(_factory.savingThrow), _factory._dc,
                                 reconcileRollTypes(target->getSavingThrowRollTypeMods(_factory.savingThrow)));
    if(!saved)
      {
        _factory._combatant->setConcentrationEffect(Effect::shared_from_this());
        target->applyCondition(Condition(Conditions::PARALYZED, _factory._combatant, this));
      }
  }

  void HoldPerson::deactivate()
  {
    _factory._combatant->breakConcentration();
    getCombatants()[0]->removeCondition(Conditions::PARALYZED, _factory._combatant);
  }

  bool HoldPerson::deactivateForCombatant(Combatant *combatant)
  {
    if(combatant == getCombatants()[0])
      {
        _factory._combatant->breakConcentration();
        getCombatants()[0]->removeCondition(Conditions::PARALYZED, _factory._combatant);
      }
    return false; // The effect ceases once the (single) target saves
  }

  bool HoldPerson::combatantSavedAtEndOfTurn(Combatant *combatant)
  {
    bool saved = rollSavingThrow(combatant->getSavingThrow(_factory.savingThrow), _factory._dc,
                                 reconcileRollTypes(combatant->getSavingThrowRollTypeMods(_factory.savingThrow)));
    return !saved; // true => failed (effect continues), false => saved (effect ends)
  }

  std::optional<CoordVector>
  HoldPerson::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *caster = _factory._combatant;
    Combatant *target = getCombatants()[0];
    if(caster->getSwallower())
      {
        return std::nullopt;
      }
    Coord currCoord = battleMap.getCombatantCoordinates(*caster).getRoot();
    if(!caster->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(*target).get(), distances, caster->getSize(),
                                                       static_cast<int>(HoldPersonFactory::range), caster->_instanceId);
      }
    else if(battleMap.getCartesianDistanceCombatants(*caster, *target) <= static_cast<int>(HoldPersonFactory::range))
      {
        return CoordVector{currCoord};
      }
    return std::nullopt;
  }
}
