#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "effects/limited_duration_effect.hpp"
#include "effects/aoe_square_effect.hpp"
#include "effects/combatant_effect.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  /**
   * Hypnotic Pattern (2024): level 3 Illusion. A swirling pattern fills a 30-foot cube within 120 feet. Each
   * creature in the area that can see the pattern makes a Wisdom save; on a failure it has the Charmed
   * condition for the duration and, while Charmed this way, it has the Incapacitated condition and a Speed of
   * 0. The effect ends for an affected creature if it takes any damage or if another creature uses an action to
   * shake it out of its stupor. Concentration, up to 1 minute. Deals no damage.
   *
   * Modeled like Faerie Fire (a Concentration cube AoE) but each failed-save creature is Charmed +
   * Incapacitated (Incapacitated already zeroes its action economy / movement) and flagged AWAKENED_BY_DMG so
   * the engine's wake-on-damage path frees it when it is hit.
   */
  class HypnoticPatternFactory : public DirectThreatFactory
  {
    friend class HypnoticPattern;

  public:
    static constexpr int level = 3;
    static constexpr SpellRange range = SpellRange::FEET_120;
    static constexpr SpellTarget target = SpellTarget::BOX_30;
    static constexpr Duration duration = Duration::MINUTE;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr SavingThrow savingThrow = SavingThrow::WIS;
    //! Heuristic threat value per enemy that would be Charmed + Incapacitated (removed from the fight).
    static constexpr double THREAT_PER_TARGET = 6.0;

    HypnoticPatternFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource);

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
  };

  class HypnoticPattern : public Actoid, public LimitedDurationEffect, public AoeSquareEffect, public CombatantEffect, public DirectThreat
  {
  public:
    HypnoticPattern(const Coord &coord, const HypnoticPatternFactory &factory)
        : Effect(factory._combatant), // Explicitly construct the virtual base
          Actoid(const_cast<HypnoticPatternFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
          LimitedDurationEffect(factory._combatant, 100),
          AoeSquareEffect(factory._combatant, coord, TRANSLATE_BOX.at(HypnoticPatternFactory::target)),
          CombatantEffect(factory._combatant, {}), _coord(coord), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    EffectType getEffectType() const override { return EffectType::HYPNOTIC_PATTERN; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;
    bool isAffecting(Combatant *combatant) const override;
    void onEnter(Combatant *combatant) override;
    void onMoveWithin(Combatant *combatant) override;
    void onExit(Combatant *combatant) override;
    void onStartOfTurn(Combatant *combatant) override;
    void onEndOfTurn(Combatant *combatant) override;

    const CoordVector &getAffectedCoords() const override { return SquareAoe::getAffectedCoords(); }

  private:
    void removeHypnoticConditions(Combatant *combatant) const;

    Coord _coord;
    const HypnoticPatternFactory &_factory;
  };
}
