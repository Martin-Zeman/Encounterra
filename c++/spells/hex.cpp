#include "spells/hex.hpp"

#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "actions/attack.hpp"
#include "spells/eldritch_blast.hpp"
#include "effects/effect_tracker.hpp"
#include <algorithm>
#include <sstream>

namespace enc
{
  HexFactory::HexFactory(AbilityType abilityType, Combatant *caster, Resource *resource)
      : ThreatModifierFactory("HexFactory", "Hex", caster, abilityType), _resource(resource)
  {
    setFlag(FactoryFlags::IS_ATTACK_MODIFIER);
  }

  std::vector<std::shared_ptr<Actoid>> HexFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    if(!_resource->hasUses(HexFactory::level) || _combatant->getSwallower())
      {
        return result;
      }
    for(auto *enemy : BattleMap::getInstance().getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(HexFactory::range)))
      {
        result.push_back(std::make_shared<Hex>(*enemy, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> HexFactory::create(void *target)
  {
    return std::make_shared<Hex>(*static_cast<Combatant *>(target), *this);
  }

  double HexFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    // The value of Hex is the extra 1d6 Necrotic on every hit against the cursed creature. Project the best
    // single attack (weapon or spell) the caster can aim at the target and measure the damage-die delta. The
    // curse persists, so future turns benefit too; weight it like Vow of Enmity (one cast empowers several
    // attacks over the spell's lifetime).
    ThreatModifiers mods;
    mods.set(ThreatModifierType::DMG_BONUS_DIE, std::vector<Die>{HexFactory::extraDmgDice});
    double maxDelta = 0.0;

    auto collect = [&](const std::vector<std::shared_ptr<ActoidFactory>> &factories) {
      for(const auto &factory : factories)
        {
          if(factory->hasFlag(FactoryFlags::IS_ATTACK_LIKE))
            {
              if(auto *directThreat = dynamic_cast<DirectThreatFactory *>(factory.get()))
                {
                  maxDelta = std::max(maxDelta, directThreat->calculateThreatToTargetDelta(target, mods));
                }
            }
        }
    };
    collect(_combatant->getActionFactoriesConst());
    collect(_combatant->getBonusActionFactoriesConst());
    collect(_combatant->getHasteActionFactoriesConst());
    return maxDelta * 3.0;
  }

  Hex::Hex(Combatant &target, HexFactory &factory)
      : Effect(factory.getCombatant(), &target),
        AttackThreatModifier(factory, ActoidFlags::IS_ATTACK_MODIFIER, AbilityType::HEX),
        CombatantEffect(factory.getCombatant(), {&target}), LimitedDurationEffect(factory.getCombatant(), HexFactory::durationRounds),
        _factory(factory)
  {}

  void Hex::activate(const Kwargs &kwargs)
  {
    EffectTracker &tracker = EffectTracker::getInstance();
    // A caster can only sustain one Hex at a time (it requires concentration); drop any prior curse first.
    for(const auto &effect : tracker.getEffectsByInitiator(_factory.getCombatant()))
      {
        if(effect->getEffectType() == EffectType::HEX)
          {
            tracker.remove(effect);
          }
      }
    tracker.add(std::dynamic_pointer_cast<Effect>(shared_from_this()));
    _factory.getCombatant()->setConcentrationEffect(std::dynamic_pointer_cast<Effect>(shared_from_this()));
  }

  void Hex::deactivate() { _factory.getCombatant()->breakConcentration(); }

  bool Hex::deactivateForCombatant(Combatant *combatant)
  {
    deactivate();
    return false;
  }

  std::string Hex::toString() const { return "Hex on " + getCombatants().front()->_name; }

  std::string Hex::shorthandStr() const { return "Hex"; }

  std::optional<CoordVector>
  Hex::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *caster = _factory.getCombatant();
    Combatant *target = getCombatants().front();
    Coord currCoord = battleMap.getCombatantCoordinates(*caster).getRoot();
    if(!caster->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(*target).get(), distances, caster->getSize(),
                                                       static_cast<int>(HexFactory::range), caster->_instanceId);
      }
    if(battleMap.getCartesianDistanceCombatants(*caster, *target) <= static_cast<int>(HexFactory::range))
      {
        return CoordVector{currCoord};
      }
    return std::nullopt;
  }

  double Hex::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(getCombatants().front(), kwargs); }

  double Hex::calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs)
  {
    auto *directThreat = dynamic_cast<DirectThreat *>(attack);
    if(attacker != _factory.getCombatant() || directThreat == nullptr)
      {
        return 0.0;
      }
    // Hex empowers both weapon attacks and spell attacks, so resolve the target from whichever kind this is.
    Combatant *attackTarget = nullptr;
    if(auto *weapon = dynamic_cast<Attack *>(attack))
      {
        attackTarget = &weapon->getTarget();
      }
    else if(auto *eldritchBlast = dynamic_cast<EldritchBlast *>(attack))
      {
        attackTarget = &eldritchBlast->getTarget();
      }
    if(attackTarget != getCombatants().front())
      {
        return 0.0;
      }
    ThreatModifiers mods;
    mods.set(ThreatModifierType::DMG_BONUS_DIE, std::vector<Die>{HexFactory::extraDmgDice});
    return directThreat->calculateThreatDelta(mods);
  }
}
