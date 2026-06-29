#include "spells/charm_person.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/teams.hpp"
#include "core/threat_utils.hpp"
#include "core/conditions.hpp"
#include "effects/effect_tracker.hpp"
#include <algorithm>
#include <iostream>
#include <limits>

namespace enc
{
  CharmPersonFactory::CharmPersonFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("CharmPersonFactory", "Charm Person", caster, abilityType), _dc(dc), _resource(resource)
  {
    setFlag(FactoryFlags::PREVENT_ENDLESS_RECURSION);
  }

  std::vector<Combatant *> CharmPersonFactory::getEligibleTargets() const
  {
    if(_combatant->getSwallower())
      {
        return {};
      }
    std::vector<Combatant *> result;
    for(auto *e : BattleMap::getInstance().getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(CharmPersonFactory::range)))
      {
        if(e->isHumanoid())
          {
            result.push_back(e);
          }
      }
    return result;
  }

  std::vector<std::shared_ptr<Actoid>> CharmPersonFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    for(auto *target : getEligibleTargets())
      {
        result.push_back(std::make_shared<CharmPerson>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> CharmPersonFactory::create(void *target)
  {
    return std::make_shared<CharmPerson>(*static_cast<Combatant *>(target), *this);
  }

  double CharmPersonFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    if(target->isAffectedBy(Conditions::CHARMED))
      {
        return 0.0;
      }
    if(BattleMap::getInstance().getCartesianDistanceCombatants(*_combatant, *target) > static_cast<int>(CharmPersonFactory::range))
      {
        return 0.0;
      }

    // Best single-target offence the charmed humanoid would otherwise turn on our team.
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

    double pFail = getSavingThrowFailProb(_dc, target->getSavingThrow(CharmPersonFactory::savingThrow));
    double pFailAcc = pFail;
    double total = 0.0;
    for(int i = 0; i < CharmPersonFactory::ROUND_HORIZON; ++i)
      {
        total += maxActionThreat * pFailAcc;
        pFailAcc *= pFail;
      }
    return total;
  }

  double CharmPersonFactory::calculateMaxThreat() const
  {
    double maxThreat = 0.0;
    for(auto *target : getEligibleTargets())
      {
        maxThreat = std::max(maxThreat, calculateThreatToTarget(target, {}));
      }
    return maxThreat;
  }

  std::string CharmPerson::toString() const { return "Charm Person on " + getCombatants()[0]->_name; }

  std::string CharmPerson::shorthandStr() const { return "Charm Person"; }

  double CharmPerson::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(getCombatants()[0], kwargs); }

  void CharmPerson::activate(const Kwargs &kwargs)
  {
    Combatant *target = getCombatants()[0];
    bool saved = rollSavingThrow(target->getSavingThrow(_factory.savingThrow), _factory._dc,
                                 reconcileRollTypes(target->getSavingThrowRollTypeMods(_factory.savingThrow)));
    if(!saved)
      {
        std::cout << target->_name << " fails the Wisdom save and is charmed by " << shorthandStr() << std::endl;
        EffectTracker::getInstance().add(std::dynamic_pointer_cast<Effect>(shared_from_this()));
        target->applyCondition(Condition(Conditions::CHARMED, _factory._combatant, this));
      }
    else
      {
        std::cout << target->_name << " succeeds on the Wisdom save against " << shorthandStr() << std::endl;
      }
  }

  void CharmPerson::deactivate() { getCombatants()[0]->removeCondition(Conditions::CHARMED, _factory._combatant); }

  bool CharmPerson::deactivateForCombatant(Combatant *combatant)
  {
    if(combatant == getCombatants()[0])
      {
        getCombatants()[0]->removeCondition(Conditions::CHARMED, _factory._combatant);
      }
    return false;
  }

  std::optional<CoordVector> CharmPerson::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *caster = _factory._combatant;
    Combatant *target = getCombatants()[0];
    Coord currCoord = battleMap.getCombatantCoordinates(*caster).getRoot();
    if(caster->getSwallower())
      {
        return std::nullopt;
      }
    if(!caster->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(*target).get(), distances, caster->getSize(),
                                                       static_cast<int>(CharmPersonFactory::range), caster->_instanceId);
      }
    if(battleMap.getCartesianDistanceCombatants(*caster, *target) <= static_cast<int>(CharmPersonFactory::range))
      {
        return CoordVector{currCoord};
      }
    return CoordVector{};
  }
}
