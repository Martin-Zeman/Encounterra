#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/combatant_effect.hpp"
#include "effects/limited_duration_effect.hpp"

namespace enc
{
  class Combatant;

  /**
   * Starry Wisp (2024): a cantrip (Radiant) ranged spell attack with a 60-foot range, dealing 1d8 Radiant
   * damage that scales with character level like other cantrips. Mirrors Firebolt. On a hit the target
   * sheds light and "can't benefit from the Invisible condition" until the caster's next turn, modeled
   * via StarryWispEffect.
   */
  class StarryWispFactory : public DirectThreatFactory
  {
    friend class StarryWisp;

  public:
    static constexpr int level = 0;
    static constexpr SpellRange range = SpellRange::FEET_60;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Radiant;

    static Die getDmgDice(int level)
    {
      if(level >= 1 && level <= 4)
        {
          return {1, 8};
        }
      else if(level >= 5 && level <= 10)
        {
          return {2, 8};
        }
      else if(level >= 11 && level <= 16)
        {
          return {3, 8};
        }
      else if(level >= 17)
        {
          return {4, 8};
        }
      else
        {
          throw std::runtime_error("Incorrect caster level of Starry Wisp");
        }
    }

    StarryWispFactory(int toHit, AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    int _toHit;
    Resource *_resource;
    Die _dmgDice;
  };

  class StarryWisp : public Actoid, public DirectThreat
  {
  public:
    StarryWisp(Combatant &target, const StarryWispFactory &factory, RollType rollType = RollType::STRAIGHT)
        : Actoid(const_cast<StarryWispFactory &>(factory), ActoidFlags::IS_SPELL | ActoidFlags::IS_ATTACK_LIKE, AbilityType::STARRY_WISP),
          _target(target), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    Combatant &getTarget() const { return _target; }
    int getToHit() const { return _factory._toHit; }
    Die getDmgDice() const { return _factory._dmgDice; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Combatant &_target;
    const StarryWispFactory &_factory;
  };

  // Applies the 2024 Starry Wisp rider on a hit: the target sheds light and "can't benefit from the
  // Invisible condition" until the start of the caster's next turn (single-turn limited-duration effect).
  class StarryWispEffect : public CombatantEffect, public LimitedDurationEffect
  {
  public:
    StarryWispEffect(Combatant *caster, Combatant *target)
        : Effect(caster), CombatantEffect(caster, {target}), LimitedDurationEffect(caster, 1)
    {}

    EffectType getEffectType() const override { return EffectType::STARRY_WISP; }
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override { return true; }
  };
}