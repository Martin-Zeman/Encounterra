#pragma once

#include "core/interfaces.hpp"
#include "core/types.hpp"
#include "core/misc.hpp"
#include "actions/action_types.hpp"
#include "effects/combatant_effect.hpp"
#include "effects/limited_duration_effect.hpp"
#include <vector>

namespace enc
{
  class Combatant;

  /**
   * Roar (Lion). The lion roars; each enemy within `range` cells makes a Wisdom saving throw against `dc` or
   * gains the Frightened condition until the start of the lion's next turn.
   *
   * Roar has no counterpart in the Python simulator (which models only the Saber-Toothed Tiger's Pounce). The
   * downstream mechanical consequences of Frightened (movement restriction, attack disadvantage) are not yet
   * wired up in this engine, so the threat value is a heuristic for the debuff and Roar simply applies the
   * condition on a failed save. Modelled as a standalone Action (rather than a "replace one attack" rider of
   * the multiattack) for simplicity.
   */
  class RoarFactory : public DirectThreatFactory
  {
    friend class Roar;

  public:
    static constexpr SavingThrow savingThrow = SavingThrow::WIS;
    //! Heuristic threat per enemy likely to be Frightened.
    static constexpr double THREAT_PER_TARGET = 2.0;

    RoarFactory(Combatant *combatant, int dc, int range);

    std::vector<Combatant *> getEligibleTargets() const;

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return std::nullopt; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

    int getDc() const { return _dc; }
    int getRange() const override { return _range; }

  private:
    int _dc;
    int _range;
  };

  class Roar : public Actoid, public DirectThreat
  {
  public:
    Roar(RoarFactory &factory) : Actoid(factory, ActoidFlags::LOCATION_INDEPENDENT, AbilityType::ROAR), _factory(factory) {}

    RoarFactory &getRoarFactory() const { return _factory; }

    std::string toString() const override;
    std::string shorthandStr() const;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

  private:
    RoarFactory &_factory;
  };

  /**
   * Effect that holds the Frightened condition applied by Roar on the combatants that failed their save,
   * removing it at the start of the roarer's next turn.
   */
  class RoarFrightenedEffect : public CombatantEffect, public LimitedDurationEffect
  {
  public:
    RoarFrightenedEffect(Combatant *roarer, const std::vector<Combatant *> &frightened)
        : Effect(roarer), CombatantEffect(roarer, frightened), LimitedDurationEffect(roarer, 1)
    {}

    EffectType getEffectType() const override { return EffectType::ROAR_FRIGHTENED; }
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;
  };
}
