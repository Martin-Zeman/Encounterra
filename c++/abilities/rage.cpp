#include "abilities/rage.hpp"
#include "core/combatant.hpp"
#include "core/teams.hpp"
#include "core/battle_map.hpp"
#include <algorithm>
#include <climits>

namespace enc
{
  namespace
  {
    // Rage lasts up to 10 rounds; the buff's benefit is projected over a short planning horizon, mirroring
    // Python's ROUND_HORIZON multiplier in abilities/rage.py.
    constexpr int ROUND_HORIZON = 3;

    // The barbarian's Strength attack factories, whose damage benefits from the Rage Damage bonus. Dex-based
    // attacks (e.g. Finesse used with Dexterity) are excluded since Rage Damage requires a Strength attack.
    std::vector<DirectThreatFactory *> getStrengthAttackFactories(Combatant *combatant)
    {
      std::vector<DirectThreatFactory *> result;
      auto collect = [&](const std::vector<std::shared_ptr<ActoidFactory>> &factories) {
        for(const auto &factory : factories)
          {
            if(!factory->hasFlag(FactoryFlags::IS_ATTACK_LIKE) || factory->hasFlag(FactoryFlags::USES_DEX))
              {
                continue;
              }
            if(auto *threatFactory = dynamic_cast<DirectThreatFactory *>(factory.get()))
              {
                result.push_back(threatFactory);
              }
          }
      };
      collect(combatant->getActionFactoriesConst());
      collect(combatant->getBonusActionFactoriesConst());
      collect(combatant->getHasteActionFactoriesConst());
      return result;
    }
  }

  RageFactory::RageFactory(Combatant *combatant, Resource *uses, RageVariant variant, AbilityType abilityType)
      : ThreatModifierFactory("RageFactory", "Rage", combatant, abilityType), _uses(uses), _variant(variant)
  {
    setFlag(FactoryFlags::IS_ATTACK_MODIFIER);
    setFlag(FactoryFlags::TARGETS_SELF);
  }

  int RageFactory::getRageBonus(int level)
  {
    if(level >= 16)
      {
        return 4;
      }
    if(level >= 9)
      {
        return 3;
      }
    return 2;
  }

  int RageFactory::getRageUses(int level)
  {
    if(level >= 20)
      {
        return INT_MAX;
      }
    if(level >= 17)
      {
        return 6;
      }
    if(level >= 12)
      {
        return 5;
      }
    if(level >= 6)
      {
        return 4;
      }
    if(level >= 3)
      {
        return 3;
      }
    return 2;
  }

  std::vector<DamageType> RageFactory::getRageResistances(RageVariant variant)
  {
    if(variant == RageVariant::BEAR)
      {
        // Bear: Resistance to every damage type except Force, Necrotic, Psychic and Radiant.
        return {DamageType::Bludgeoning, DamageType::Piercing, DamageType::Slashing, DamageType::Fire,
                DamageType::Cold,        DamageType::Poison,   DamageType::Acid,     DamageType::Lightning,
                DamageType::Thunder};
      }
    // Base Rage (and the Eagle/Wolf aspects, whose extra benefit is mobility / ally support).
    return {DamageType::Bludgeoning, DamageType::Piercing, DamageType::Slashing};
  }

  std::vector<std::shared_ptr<Actoid>> RageFactory::createAll(void *previousActionInDag) { return {std::make_shared<Rage>(*this)}; }

  std::shared_ptr<Actoid> RageFactory::create(void *target) { return std::make_shared<Rage>(*this); }

  double RageFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    const int rageBonus = getRageBonus(_combatant->getLevel());

    // Best damage increase the Rage Damage bonus grants to one of the barbarian's Strength attacks.
    ThreatModifiers mods;
    mods.set(ThreatModifierType::DMG_BONUS_FLAT, rageBonus);
    double maxOutgoing = 0.0;
    for(auto *attackFactory : getStrengthAttackFactories(_combatant))
      {
        maxOutgoing = std::max(maxOutgoing, attackFactory->calculateThreatToTargetDelta(target, mods));
      }

    double total = maxOutgoing;

    // Heuristic for the damage the barbarian would resist from this enemy. The Bear aspect resists almost
    // everything, so its incoming-threat reduction is weighted far more heavily than the base B/P/S Resistance.
    const double divisor = (_variant == RageVariant::BEAR) ? 1.2 : 3.0;

    auto bestIncoming = [&](const std::vector<std::shared_ptr<ActoidFactory>> &factories) {
      double maxIncoming = 0.0;
      for(const auto &factory : factories)
        {
          if(!factory->hasFlag(FactoryFlags::IS_DIRECT_THREAT))
            {
              continue;
            }
          if(auto *threatFactory = dynamic_cast<DirectThreatFactory *>(factory.get()))
            {
              maxIncoming = std::max(maxIncoming, threatFactory->calculateThreatToTarget(_combatant, {}));
            }
        }
      return maxIncoming;
    };

    total += bestIncoming(target->getActionFactoriesConst()) / divisor;
    total += bestIncoming(target->getBonusActionFactoriesConst()) / divisor;

    return total * ROUND_HORIZON;
  }

  double RageFactory::calculateMaxThreat() const
  {
    Teams &teams = Teams::getInstance();
    double maxThreat = 0.0;
    for(auto *enemy : teams.getAliveNonSwallowedEnemies(*_combatant))
      {
        maxThreat = std::max(maxThreat, calculateThreatToTarget(enemy, {}));
      }
    return maxThreat;
  }

  Rage::Rage(RageFactory &factory)
      : Effect(factory.getCombatant()),
        AttackThreatModifier(factory, ActoidFlags::LOCATION_INDEPENDENT | ActoidFlags::IS_PRIORITY, factory.getAbilityType()),
        CombatantEffect(factory.getCombatant(), {factory.getCombatant()}), LimitedDurationEffect(factory.getCombatant(), MAX_RAGE_ROUNDS),
        _factory(factory), _rageBonus(RageFactory::getRageBonus(factory.getCombatant()->getLevel()))
  {}

  EffectType Rage::getEffectType() const { return EffectType::RAGE; }

  void Rage::activate(const Kwargs &kwargs)
  {
    if(_active)
      {
        return;
      }
    Combatant *barbarian = _factory.getCombatant();
    barbarian->addAbilityDmgBonus(_rageBonus);
    for(DamageType dmgType : RageFactory::getRageResistances(_factory.getVariant()))
      {
        barbarian->addResistance(dmgType);
      }
    // Eagle: the barbarian Dashes and Disengages as part of entering the Rage, gaining extra movement equal
    // to its Speed and ignoring opportunity attacks for the move.
    if(_factory.getVariant() == RageVariant::EAGLE)
      {
        barbarian->setMovement(barbarian->getMovement() + barbarian->getSpeed());
        barbarian->setDisengaging(true);
      }
    // Entering the Rage counts as the first qualifying event, so it survives at least one start-of-turn tick.
    _extendedThisTurn = true;
    _active = true;
  }

  void Rage::deactivate()
  {
    if(!_active)
      {
        return;
      }
    Combatant *barbarian = _factory.getCombatant();
    barbarian->addAbilityDmgBonus(-_rageBonus);
    for(DamageType dmgType : RageFactory::getRageResistances(_factory.getVariant()))
      {
        barbarian->removeResistance(dmgType);
      }
    _active = false;
  }

  bool Rage::deactivateForCombatant(Combatant *combatant)
  {
    // Rage only affects the barbarian itself.
    deactivate();
    return true;
  }

  bool Rage::startOfTurnTick()
  {
    // 2024: the Rage lasts until the end of the barbarian's next turn. It carries into a new turn only if it
    // was extended (an attack, a forced save, or a Bonus Action) during the previous turn, up to a 10-minute
    // cap. Each surviving round requires a fresh qualifying event.
    if(--_roundsRemaining <= 0 || !_extendedThisTurn)
      {
        return false;
      }
    _extendedThisTurn = false;
    return true;
  }

  std::string Rage::toString() const
  {
    return "Rage of " + _factory.getCombatant()->_name;
  }

  std::string Rage::shorthandStr() const { return "Rage"; }

  std::optional<CoordVector>
  Rage::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    // Entering a Rage is location independent; it is always available from the barbarian's current position.
    return CoordVector{BattleMap::getInstance().getCombatantCoordinates(*_factory.getCombatant()).getRoot()};
  }

  double Rage::calculateThreat(const Kwargs &kwargs)
  {
    // Survival heuristic: the Resistance roughly halves incoming damage, valued against the barbarian's
    // current hit points (mirrors Python's Rage.calculate_threat returning curr_hp / 2).
    return _factory.getCombatant()->getCurrentHp() / 2.0;
  }

  double Rage::calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs)
  {
    if(attack == nullptr || !attack->getFactory().hasFlag(FactoryFlags::IS_MELEE))
      {
        return 0.0;
      }
    auto *directThreat = dynamic_cast<DirectThreat *>(attack);
    if(directThreat == nullptr)
      {
        return 0.0;
      }
    ThreatModifiers mods;
    mods.set(ThreatModifierType::DMG_BONUS_FLAT, _rageBonus);
    return directThreat->calculateThreatDelta(mods);
  }
}
