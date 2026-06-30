#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/limited_duration_effect.hpp"
#include "effects/combatant_effect.hpp"

namespace enc
{
  class Combatant;

  /**
   * Blink (2024): level 3 Transmutation, cast as an Action on self. Roll a d6 at the end of each of the
   * caster's turns; on a 4-6 the caster vanishes into the Border Ethereal until the start of its next turn,
   * during which it can't be targeted or affected by anything on the material plane. Lasts 1 minute, no
   * Concentration.
   *
   * Modeled as a self-targeting buff: at the end of the caster's turn a d6 decides whether the caster becomes
   * ethereal (untargetable), and at the start of its next turn it returns. The untargetability is enforced by
   * excluding an ethereal combatant from enemy/ally target lists (see Combatant::isEtherealUntargetable).
   */
  class BlinkFactory : public DirectThreatFactory
  {
    friend class Blink;

  public:
    static constexpr int level = 3;
    static constexpr SpellRange range = SpellRange::SELF;
    static constexpr SpellTarget target = SpellTarget::SELF;
    static constexpr Duration duration = Duration::MINUTE;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::BUFF;
    //! Radius (in cells) within which nearby enemies contribute to the defensive value of becoming
    //! untargetable.
    static constexpr int THREAT_RADIUS = 12;
    //! Probability that, at the end of each of the caster's turns, the d6 sends it into the Border Ethereal
    //! (a roll of 4-6), making it untargetable until the start of its next turn. Roughly the fraction of the
    //! enemies' attacks that Blink causes to miss outright.
    static constexpr double ETHEREAL_PROB = 0.5;

    BlinkFactory(AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    Resource *_resource;
  };

  class Blink : public Actoid, public LimitedDurationEffect, public CombatantEffect, public DirectThreat
  {
  public:
    Blink(const BlinkFactory &factory)
        : Effect(factory._combatant), Actoid(const_cast<BlinkFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
          LimitedDurationEffect(factory._combatant, 100), CombatantEffect(factory._combatant, {factory._combatant}), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;
    EffectType getEffectType() const override { return EffectType::BLINK; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;

    //! At the start of the caster's turn it returns from the Border Ethereal to the material plane.
    bool startOfTurnForCombatant(Combatant *combatant) override;
    //! At the end of the caster's turn, roll a d6: on a 4-6 the caster blinks out and becomes untargetable.
    bool combatantSavedAtEndOfTurn(Combatant *combatant) override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    const BlinkFactory &_factory;
  };
}
