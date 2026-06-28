#include "spells/bless.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
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

  BlessFactory::BlessFactory(AbilityType abilityType, Combatant *caster, Resource *resource)
      : ThreatModifierFactory("BlessFactory", "Bless", caster, abilityType), _resource(resource)
  {
    setFlag(FactoryFlags::IS_ATTACK_MODIFIER);
  }

  std::vector<std::vector<Combatant *>> BlessFactory::getEligibleTargetGroups() const
  {
    std::vector<Combatant *> targets;
    if(_combatant->getSwallower())
      {
        targets.push_back(_combatant);
      }
    else
      {
        targets = BattleMap::getInstance().getNonSwallowedAlliesWithinRadius(_combatant, static_cast<int>(BlessFactory::range));
        targets.push_back(_combatant);
      }

    std::vector<std::vector<Combatant *>> groups;
    std::vector<Combatant *> current;
    for(std::size_t groupSize = 1; groupSize <= std::min<std::size_t>(3, targets.size()); ++groupSize)
      {
        addGroups(targets, groupSize, 0, current, groups);
      }
    return groups;
  }

  std::vector<std::shared_ptr<Actoid>> BlessFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    for(auto &group : getEligibleTargetGroups())
      {
        result.push_back(std::make_shared<Bless>(std::move(group), *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> BlessFactory::create(void *target)
  {
    auto *targets = static_cast<std::vector<Combatant *> *>(target);
    return std::make_shared<Bless>(*targets, *this);
  }

  double BlessFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    ThreatModifiers mods;
    mods.set(ThreatModifierType::TO_HIT_DIE, Bless::bonusDie);
    return bestAttackDeltaFor(target, mods) * BlessFactory::SAVING_THROW_BONUS_MULTIPLIER * BlessFactory::ROUND_HORIZON;
  }

  Bless::Bless(std::vector<Combatant *> targets, BlessFactory &factory)
      : Effect(factory.getCombatant()), AttackThreatModifier(factory, ActoidFlags::IS_SPELL | ActoidFlags::IS_ATTACK_MODIFIER, factory._abilityType),
        CombatantEffect(factory.getCombatant(), std::move(targets)), LimitedDurationEffect(factory.getCombatant(), 10), _factory(factory)
  {}

  void Bless::activate(const Kwargs &kwargs)
  {
    for(auto *target : _combatants)
      {
        target->addToHitDiceMod(Bless::bonusDie);
        for(SavingThrow savingThrow : {SavingThrow::STR, SavingThrow::DEX, SavingThrow::CON, SavingThrow::INT, SavingThrow::WIS, SavingThrow::CHA})
          {
            target->addSavingThrowDiceMod(savingThrow, Bless::bonusDie);
          }
      }
    _factory.getCombatant()->setConcentrationEffect(std::dynamic_pointer_cast<Effect>(shared_from_this()));
  }

  void Bless::deactivate()
  {
    for(auto *target : _combatants)
      {
        target->removeToHitDiceMod(Bless::bonusDie);
        for(SavingThrow savingThrow : {SavingThrow::STR, SavingThrow::DEX, SavingThrow::CON, SavingThrow::INT, SavingThrow::WIS, SavingThrow::CHA})
          {
            target->removeSavingThrowDiceMod(savingThrow, Bless::bonusDie);
          }
      }
    _factory.getCombatant()->breakConcentration();
  }

  bool Bless::deactivateForCombatant(Combatant *combatant)
  {
    combatant->removeToHitDiceMod(Bless::bonusDie);
    for(SavingThrow savingThrow : {SavingThrow::STR, SavingThrow::DEX, SavingThrow::CON, SavingThrow::INT, SavingThrow::WIS, SavingThrow::CHA})
      {
        combatant->removeSavingThrowDiceMod(savingThrow, Bless::bonusDie);
      }
    _combatants.erase(std::remove(_combatants.begin(), _combatants.end(), combatant), _combatants.end());
    return !_combatants.empty();
  }

  std::string Bless::toString() const
  {
    std::ostringstream out;
    out << "Bless on ";
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

  std::string Bless::shorthandStr() const { return "Bless"; }

  double Bless::calculateThreat(const Kwargs &kwargs)
  {
    double total = 0.0;
    for(auto *target : _combatants)
      {
        total += _factory.calculateThreatToTarget(target, kwargs);
      }
    return total;
  }

  double Bless::calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs)
  {
    if(std::find(_combatants.begin(), _combatants.end(), attacker) == _combatants.end())
      {
        return 0.0;
      }
    if(auto *direct = dynamic_cast<DirectThreat *>(attack))
      {
        ThreatModifiers mods;
        mods.set(ThreatModifierType::TO_HIT_DIE, Bless::bonusDie);
        return direct->calculateThreatDelta(mods);
      }
    return 0.0;
  }

  std::optional<CoordVector> Bless::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *caster = _factory.getCombatant();
    Coord currCoord = battleMap.getCombatantCoordinates(*caster).getRoot();
    if(caster->getSwallower())
      {
        return CoordVector{currCoord};
      }
    if(caster->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        for(auto *target : _combatants)
          {
            if(battleMap.getCartesianDistanceCombatants(*caster, *target) > static_cast<int>(BlessFactory::range))
              {
                return CoordVector{};
              }
          }
        return CoordVector{currCoord};
      }

    std::unordered_set<Coord> intersection;
    bool first = true;
    for(auto *target : _combatants)
      {
        CoordVector coords = battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(*target).get(), distances, caster->getSize(),
                                                                     static_cast<int>(BlessFactory::range), caster->_instanceId);
        if(first)
          {
            intersection.insert(coords.begin(), coords.end());
            first = false;
          }
        else
          {
            for(auto it = intersection.begin(); it != intersection.end();)
              {
                if(std::find(coords.begin(), coords.end(), *it) == coords.end())
                  {
                    it = intersection.erase(it);
                  }
                else
                  {
                    ++it;
                  }
              }
          }
      }
    return CoordVector(intersection.begin(), intersection.end());
  }
}
