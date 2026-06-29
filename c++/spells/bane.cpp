#include "spells/bane.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/threat_utils.hpp"
#include "effects/effect_tracker.hpp"
#include <algorithm>
#include <sstream>
#include <unordered_set>

namespace enc
{
  namespace
  {
    void addGroups(const std::vector<Combatant *> &targets, std::size_t groupSize, std::size_t start, std::vector<Combatant *> &current,
                   std::vector<std::vector<Combatant *>> &groups)
    {
      if(current.size() == groupSize)
        {
          groups.push_back(current);
          return;
        }
      for(std::size_t i = start; i < targets.size(); ++i)
        {
          current.push_back(targets[i]);
          addGroups(targets, groupSize, i + 1, current, groups);
          current.pop_back();
        }
    }

    double bestAttackDeltaFor(Combatant *combatant, const ThreatModifiers &mods)
    {
      double best = 0.0;
      auto collect = [&](const std::vector<std::shared_ptr<ActoidFactory>> &factories) {
        for(const auto &factory : factories)
          {
            if(auto *direct = dynamic_cast<DirectThreatFactory *>(factory.get()))
              {
                if(factory->hasFlag(FactoryFlags::IS_ATTACK_LIKE))
                  {
                    for(auto *target : BattleMap::getInstance().getNonSwallowedEnemiesWithinRadius(combatant, direct->getRange()))
                      {
                        best = std::max(best, direct->calculateThreatToTargetDelta(target, mods));
                      }
                  }
              }
          }
      };
      collect(combatant->getActionFactoriesConst());
      collect(combatant->getBonusActionFactoriesConst());
      collect(combatant->getHasteActionFactoriesConst());
      return best;
    }
  }

  BaneFactory::BaneFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : ThreatModifierFactory("BaneFactory", "Bane", caster, abilityType), _dc(dc), _resource(resource)
  {
    setFlag(FactoryFlags::IS_ATTACK_MODIFIER);
  }

  std::vector<std::vector<Combatant *>> BaneFactory::getEligibleTargetGroups() const
  {
    std::vector<Combatant *> targets = BattleMap::getInstance().getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(BaneFactory::range));

    std::vector<std::vector<Combatant *>> groups;
    std::vector<Combatant *> current;
    for(std::size_t groupSize = 1; groupSize <= std::min<std::size_t>(3, targets.size()); ++groupSize)
      {
        addGroups(targets, groupSize, 0, current, groups);
      }
    return groups;
  }

  std::vector<std::shared_ptr<Actoid>> BaneFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    for(auto &group : getEligibleTargetGroups())
      {
        result.push_back(std::make_shared<Bane>(std::move(group), *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> BaneFactory::create(void *target)
  {
    auto *targets = static_cast<std::vector<Combatant *> *>(target);
    return std::make_shared<Bane>(*targets, *this);
  }

  double BaneFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    // Only enemies that fail the Charisma save are debuffed; weight the value by the chance of failure.
    double failProb = getSavingThrowFailProb(_dc, target->getSavingThrow(BaneFactory::savingThrow));
    ThreatModifiers mods;
    mods.set(ThreatModifierType::TO_HIT_DIE, Bane::penaltyDie);
    return bestAttackDeltaFor(target, mods) * BaneFactory::ROUND_HORIZON * failProb;
  }

  Bane::Bane(std::vector<Combatant *> targets, BaneFactory &factory)
      : Effect(factory.getCombatant()), AttackThreatModifier(factory, ActoidFlags::IS_SPELL | ActoidFlags::IS_ATTACK_MODIFIER, factory._abilityType),
        CombatantEffect(factory.getCombatant(), std::move(targets)), LimitedDurationEffect(factory.getCombatant(), 10), _factory(factory)
  {}

  void Bane::applyPenalties(Combatant *combatant)
  {
    for(SavingThrow savingThrow : {SavingThrow::STR, SavingThrow::DEX, SavingThrow::CON, SavingThrow::INT, SavingThrow::WIS, SavingThrow::CHA})
      {
        combatant->addSavingThrowFlatMod(savingThrow, BaneFactory::FLAT_PENALTY);
      }
  }

  void Bane::removePenalties(Combatant *combatant)
  {
    for(SavingThrow savingThrow : {SavingThrow::STR, SavingThrow::DEX, SavingThrow::CON, SavingThrow::INT, SavingThrow::WIS, SavingThrow::CHA})
      {
        combatant->addSavingThrowFlatMod(savingThrow, -BaneFactory::FLAT_PENALTY);
      }
  }

  void Bane::activate(const Kwargs &kwargs)
  {
    // Targets that succeed on the Charisma save shrug off Bane; only the failures are debuffed.
    std::vector<Combatant *> affected;
    for(auto *target : _combatants)
      {
        bool saved = rollSavingThrow(target->getSavingThrow(BaneFactory::savingThrow), getDc(),
                                     reconcileRollTypes(target->getSavingThrowRollTypeMods(BaneFactory::savingThrow)));
        if(!saved)
          {
            applyPenalties(target);
            affected.push_back(target);
            std::cout << target->_name << " failed the save and is affected by Bane." << std::endl;
          }
          else{
            std::cout << target->_name << " saved against Bane." << std::endl;
          }
      }
    _combatants = std::move(affected);
    if(!_combatants.empty())
      {
        _factory.getCombatant()->setConcentrationEffect(std::dynamic_pointer_cast<Effect>(shared_from_this()));
      }
  }

  void Bane::deactivate()
  {
    for(auto *target : _combatants)
      {
        removePenalties(target);
      }
    _factory.getCombatant()->breakConcentration();
  }

  bool Bane::deactivateForCombatant(Combatant *combatant)
  {
    removePenalties(combatant);
    _combatants.erase(std::remove(_combatants.begin(), _combatants.end(), combatant), _combatants.end());
    return !_combatants.empty();
  }

  std::string Bane::toString() const
  {
    std::ostringstream out;
    out << "Bane on ";
    for(std::size_t i = 0; i < _combatants.size(); ++i)
      {
        if(i > 0)
          {
            out << (i + 1 == _combatants.size() ? " and " : ", ");
          }
        out << _combatants[i]->_name;
      }
    return out.str();
  }

  std::string Bane::shorthandStr() const { return "Bane"; }

  double Bane::calculateThreat(const Kwargs &kwargs)
  {
    double total = 0.0;
    for(auto *target : _combatants)
      {
        total += _factory.calculateThreatToTarget(target, kwargs);
      }
    return total;
  }

  std::optional<CoordVector> Bane::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *caster = _factory.getCombatant();
    Coord currCoord = battleMap.getCombatantCoordinates(*caster).getRoot();
    for(auto *target : _combatants)
      {
        if(battleMap.getCartesianDistanceCombatants(*caster, *target) > static_cast<int>(BaneFactory::range))
          {
            return CoordVector{};
          }
      }
    return CoordVector{currCoord};
  }
}
