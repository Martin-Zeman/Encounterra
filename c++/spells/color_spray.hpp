#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/limited_duration_effect.hpp"
#include "effects/aoe_spheric_effect.hpp"
#include "effects/combatant_effect.hpp"

namespace enc
{
  class Combatant;

  // --- Description (Color Spray, 1st-level Illusion) ---
  // Casting Time: Action | Range: Self (15-foot Cone) | Components: V, S, M (red, yellow, and blue powder)
  // Duration: Instantaneous. You launch a dazzling array of flashing, colorful light. Each creature in a 15-foot
  // Cone must succeed on a Constitution saving throw or have the Blinded condition until the end of your next
  // turn. At Higher Levels: deals no additional effect at higher slots in 2024 rules.

  // Color Spray (2024): level 1 illusion. A burst of dazzling colours blinds creatures around the caster. We
  // approximate the cone as a 10-foot self-centred burst: each enemy in the area makes a Constitution save or
  // is Blinded until the end of the caster's next turn (one round). No concentration, no damage.
  class ColorSprayFactory : public DirectThreatFactory
  {
    friend class ColorSpray;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::SELF;
    static constexpr SpellTarget target = SpellTarget::RADIUS_10;
    static constexpr Duration duration = Duration::ROUND_ONE;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr SavingThrow savingThrow = SavingThrow::CON;
    //! Heuristic threat value per enemy blinded (blinded foes attack at disadvantage, allies hit easier).
    static constexpr double THREAT_PER_TARGET = 3.0;

    ColorSprayFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateMaxThreat() const override;

  private:
    int _dc;
    Resource *_resource;
  };

  class ColorSpray : public Actoid, public LimitedDurationEffect, public AoeSphericEffect, public CombatantEffect, public DirectThreat
  {
  public:
    ColorSpray(const Coord &coord, const ColorSprayFactory &factory)
        : Effect(factory._combatant), AoeEffect(factory._combatant),
          Actoid(const_cast<ColorSprayFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
          LimitedDurationEffect(factory._combatant, 1), AoeSphericEffect(factory._combatant, coord, TRANSLATE_RADIUS.at(ColorSprayFactory::target)),
          CombatantEffect(factory._combatant, {}), _coord(coord), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    EffectType getEffectType() const override { return EffectType::COLOR_SPRAY; }

    double calculateThreat(const Kwargs &kwargs) override;

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

    const CoordVector &getAffectedCoords() const override { return SphericAoe::getAffectedCoords(); }

  private:
    Coord _coord;
    const ColorSprayFactory &_factory;
  };
}
