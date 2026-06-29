#include "abilities/bardic_inspiration.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "effects/effect_tracker.hpp"
#include <algorithm>
#include <sstream>

namespace enc
{
  namespace
  {
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

  BardicInspirationFactory::BardicInspirationFactory(AbilityType abilityType, Combatant *caster, Resource *resource)
      : ThreatModifierFactory("BardicInspirationFactory", "Bardic Inspiration", caster, abilityType), _resource(resource)
  {
    setFlag(FactoryFlags::IS_ATTACK_MODIFIER);
  }

  std::vector<Combatant *> BardicInspirationFactory::getEligibleTargets() const
  {
    if(_combatant->getSwallower())
      {
        return {_combatant};
      }
    auto targets = BattleMap::getInstance().getNonSwallowedAlliesWithinRadius(_combatant, static_cast<int>(BardicInspirationFactory::range));
    targets.push_back(_combatant);
    return targets;
  }

  std::vector<std::shared_ptr<Actoid>> BardicInspirationFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    for(auto *target : getEligibleTargets())
      {
        result.push_back(std::make_shared<BardicInspiration>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> BardicInspirationFactory::create(void *target)
  {
    return std::make_shared<BardicInspiration>(*static_cast<Combatant *>(target), *this);
  }

  double BardicInspirationFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    ThreatModifiers mods;
    mods.set(ThreatModifierType::TO_HIT_DIE, BardicInspirationFactory::inspirationDie);
    return bestAttackDeltaFor(target, mods) * BardicInspirationFactory::SAVING_THROW_BONUS_MULTIPLIER;
  }

  BardicInspiration::BardicInspiration(Combatant &target, BardicInspirationFactory &factory)
      : Effect(factory.getCombatant()),
        AttackThreatModifier(factory, ActoidFlags::IS_SPELL | ActoidFlags::IS_ATTACK_MODIFIER, factory._abilityType),
        CombatantEffect(factory.getCombatant(), {&target}), LimitedDurationEffect(factory.getCombatant(), 10), _factory(factory)
  {}

  void BardicInspiration::activate(const Kwargs &kwargs)
  {
    for(auto *target : _combatants)
      {
        target->addToHitDiceMod(BardicInspirationFactory::inspirationDie);
        for(SavingThrow savingThrow : {SavingThrow::STR, SavingThrow::DEX, SavingThrow::CON, SavingThrow::INT, SavingThrow::WIS, SavingThrow::CHA})
          {
            target->addSavingThrowDiceMod(savingThrow, BardicInspirationFactory::inspirationDie);
          }
      }
  }

  void BardicInspiration::deactivate()
  {
    for(auto *target : _combatants)
      {
        target->removeToHitDiceMod(BardicInspirationFactory::inspirationDie);
        for(SavingThrow savingThrow : {SavingThrow::STR, SavingThrow::DEX, SavingThrow::CON, SavingThrow::INT, SavingThrow::WIS, SavingThrow::CHA})
          {
            target->removeSavingThrowDiceMod(savingThrow, BardicInspirationFactory::inspirationDie);
          }
      }
  }

  bool BardicInspiration::deactivateForCombatant(Combatant *combatant)
  {
    combatant->removeToHitDiceMod(BardicInspirationFactory::inspirationDie);
    for(SavingThrow savingThrow : {SavingThrow::STR, SavingThrow::DEX, SavingThrow::CON, SavingThrow::INT, SavingThrow::WIS, SavingThrow::CHA})
      {
        combatant->removeSavingThrowDiceMod(savingThrow, BardicInspirationFactory::inspirationDie);
      }
    _combatants.erase(std::remove(_combatants.begin(), _combatants.end(), combatant), _combatants.end());
    return !_combatants.empty();
  }

  std::string BardicInspiration::toString() const { return "Bardic Inspiration on " + _combatants.front()->_name; }

  std::string BardicInspiration::shorthandStr() const { return "Bardic Inspiration"; }

  double BardicInspiration::calculateThreat(const Kwargs &kwargs)
  {
    double total = 0.0;
    for(auto *target : _combatants)
      {
        total += _factory.calculateThreatToTarget(target, kwargs);
      }
    return total;
  }

  double BardicInspiration::calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs)
  {
    if(std::find(_combatants.begin(), _combatants.end(), attacker) == _combatants.end())
      {
        return 0.0;
      }
    if(auto *direct = dynamic_cast<DirectThreat *>(attack))
      {
        ThreatModifiers mods;
        mods.set(ThreatModifierType::TO_HIT_DIE, BardicInspirationFactory::inspirationDie);
        return direct->calculateThreatDelta(mods);
      }
    return 0.0;
  }

  std::optional<CoordVector> BardicInspiration::getEligibleCoords(const blaze::DynamicVector<int> &distances,
                                                                  const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    return CoordVector{BattleMap::getInstance().getCombatantCoordinates(*_factory.getCombatant()).getRoot()};
  }
}
