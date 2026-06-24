#pragma once

#include "core/interfaces.hpp"
#include "core/types.hpp"
#include "core/misc.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/combatant_effect.hpp"
#include "effects/limited_duration_effect.hpp"
#include <vector>

namespace enc
{
  class Combatant;

  //! Rage of the Wilds (Path of the Wild Heart, 2024): when the barbarian enters its Rage it chooses one
  //! animal aspect. Each is offered to the planner as a separate Rage bonus action sharing the same pool of
  //! Rage uses.
  //!   - BASE  : plain Rage (Resistance to Bludgeoning/Piercing/Slashing) — used by non-Wild-Heart barbarians.
  //!   - BEAR  : Resistance to every damage type except Force, Necrotic, Psychic and Radiant.
  //!   - EAGLE : on entering the Rage the barbarian also Dashes (and may Disengage), gaining extra movement.
  //!   - WOLF  : while raging, the barbarian's allies have Advantage on attack rolls against enemies within
  //!             5 ft of the barbarian.
  enum class RageVariant
  {
    BASE,
    BEAR,
    EAGLE,
    WOLF
  };

  /**
   * Rage (2024). A self-targeting buff modelled as a ThreatModifierFactory (mirroring Python's
   * abilities/rage.py): the threat it generates is the best damage increase its Rage Damage bonus grants to
   * one of the barbarian's Strength attacks plus a heuristic for the damage it would resist, projected over a
   * short planning horizon. It does NOT set IS_DIRECT_THREAT, so it does not recurse into the threat-delta
   * loops of other modifiers.
   */
  class RageFactory : public ThreatModifierFactory
  {
    friend class Rage;

  public:
    RageFactory(Combatant *combatant, Resource *uses, RageVariant variant, AbilityType abilityType = AbilityType::RAGE);

    //! Rage Damage bonus by Barbarian level (Barbarian Features table).
    static int getRageBonus(int level);
    //! Number of Rage uses by Barbarian level.
    static int getRageUses(int level);
    //! Damage types the barbarian resists while raging with the given aspect.
    static std::vector<DamageType> getRageResistances(RageVariant variant);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _uses; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateMaxThreat() const;

    RageVariant getVariant() const { return _variant; }

  private:
    Resource *_uses;
    RageVariant _variant;
  };

  class Rage : public AttackThreatModifier, public CombatantEffect, public LimitedDurationEffect
  {
  public:
    explicit Rage(RageFactory &factory);

    EffectType getEffectType() const override;
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;

    //! 2024 duration: the Rage lasts until the end of the barbarian's next turn and persists into a new turn
    //! only if it was extended (an attack roll, a forced saving throw, or a Bonus Action) during the previous
    //! turn. Maintained for at most 10 minutes (100 rounds).
    bool startOfTurnTick() override;
    //! Record a Rage-extending event (called when the barbarian attacks or forces a save this turn).
    void markExtended() { _extendedThisTurn = true; }

    RageVariant getVariant() const { return _factory.getVariant(); }

    std::string toString() const override;
    std::string shorthandStr() const;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) override;

  private:
    static constexpr int MAX_RAGE_ROUNDS = 100; // 10 minutes, the hard cap on a single Rage.
    RageFactory &_factory;
    int _rageBonus;
    bool _active = false;
    bool _extendedThisTurn = false;
    int _roundsRemaining = MAX_RAGE_ROUNDS;
  };
}
