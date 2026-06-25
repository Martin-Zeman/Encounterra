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
   * Moonbeam (2024): level 2. A 5-foot-radius, 40-foot-high cylinder of moonlight appears within 120 feet.
   * When a creature enters the area or starts its turn there, it makes a Constitution save, taking 2d10
   * Radiant damage on a failure (half on a success). Concentration, up to 1 minute (10 rounds). The caster
   * can move the beam up to 60 feet as an action on later turns (the relocation is not modeled here; the
   * beam is treated as stationary, mirroring Spike Growth).
   */
  class MoonbeamFactory : public DirectThreatFactory
  {
    friend class Moonbeam;

  public:
    static constexpr int level = 2;
    static constexpr SpellRange range = SpellRange::FEET_120;
    static constexpr SpellTarget target = SpellTarget::RADIUS_5;
    static constexpr Duration duration = Duration::MINUTE;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Radiant;

    MoonbeamFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource);

    Coord findBestArgs() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    int _dc;
    Resource *_resource;
    SavingThrow _savingThrow;
    std::vector<Die> _dmgDice;
  };

  class Moonbeam : public Actoid, public LimitedDurationEffect, public AoeSphericEffect, public DirectThreat
  {
  public:
    Moonbeam(const Coord &coord, const MoonbeamFactory &factory)
        : Effect(factory._combatant),    // Explicitly construct the virtual base
          AoeEffect(factory._combatant), // Explicitly construct the virtual base
          Actoid(const_cast<MoonbeamFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
          LimitedDurationEffect(factory._combatant, 100),
          AoeSphericEffect(factory._combatant, coord, TRANSLATE_RADIUS.at(MoonbeamFactory::target)), _coord(coord), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    EffectType getEffectType() const override { return EffectType::MOONBEAM; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;
    void onEnter(Combatant *combatant) override;
    void onMoveWithin(Combatant *combatant) override;
    void onExit(Combatant *combatant) override;
    void onStartOfTurn(Combatant *combatant) override;
    void onEndOfTurn(Combatant *combatant) override;

    double threatOnEnter(Combatant *target, const Kwargs &kwargs) const override;
    double threatOnStartOfTurn(Combatant *target, const Kwargs &kwargs) const override;

    const CoordVector &getAffectedCoords() const { return SphericAoe::getAffectedCoords(); }

  private:
    void applyMoonlight(Combatant *combatant);

    Coord _coord;
    const MoonbeamFactory &_factory;
  };
}
