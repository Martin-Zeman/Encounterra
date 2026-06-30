#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/limited_duration_effect.hpp"
#include "effects/aoe_spheric_effect.hpp"

namespace enc
{
  class Combatant;

  /**
   * Darkness (2024): level 2 Evocation. A 15-foot-radius sphere of magical darkness spreads from a point
   * within 60 feet for the duration (Concentration, up to 10 minutes). A creature inside the area is
   * effectively Blinded (it can't see), since it is engulfed in darkness that even Darkvision can't penetrate.
   * Deals no damage.
   *
   * This engine has no lighting model, so Darkness is represented as a Blinding sphere: every creature inside
   * the area is Blinded for as long as it remains there, EXCEPT creatures that can see through magical darkness
   * (the Devil's Sight invocation). That asymmetry is exactly what makes Darkness valuable to a warlock who has
   * taken Devil's Sight: its enemies are Blinded while it is not.
   *
   * It is modeled as a threat MODIFIER rather than a direct-damage threat: its value comes entirely from the
   * roll-type changes the Blinded condition produces. A Blinded enemy attacks at disadvantage (reducing the
   * damage it deals the caster), and a caster with Devil's Sight attacks a Blinded enemy with advantage.
   */
  class DarknessFactory : public ThreatModifierFactory
  {
    friend class Darkness;

  public:
    static constexpr int level = 2;
    static constexpr SpellRange range = SpellRange::FEET_60;
    static constexpr SpellTarget target = SpellTarget::RADIUS_15;
    static constexpr Duration duration = Duration::TEN_MINUTES;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::HARMFUL;

    DarknessFactory(AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateMaxThreat() const;

  private:
    Resource *_resource;
  };

  class Darkness : public Actoid, public LimitedDurationEffect, public AoeSphericEffect, public DirectThreat
  {
  public:
    Darkness(const Coord &coord, const DarknessFactory &factory);

    std::string toString() const override;
    std::string shorthandStr() const;

    void onStartOfTurn(Combatant *combatant) override;
    void onEndOfTurn(Combatant *combatant) override;
    void onEnter(Combatant *combatant) override;
    void onMoveWithin(Combatant *combatant) override;
    void onExit(Combatant *combatant) override;

    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;
    EffectType getEffectType() const override;

    const CoordVector &getAffectedCoords() const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    //! A creature is Blinded by the darkness unless it can see through magical darkness (Devil's Sight).
    static bool isBlindedByDarkness(Combatant *combatant);

    Coord _coord;
    const DarknessFactory &_factory;
  };
}
