#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/limited_duration_effect.hpp"
#include "effects/aoe_square_effect.hpp"
#include "effects/combatant_effect.hpp"

namespace enc
{
  class Combatant;

  /**
   * Faerie Fire (2024): level 1, a 20-foot cube within 60 feet. Each creature in the area makes a Dexterity
   * save; on a failure it is outlined in light (loses the benefit of being Invisible) and attack rolls
   * against it have advantage for the duration. Concentration, up to 1 minute (10 rounds). Deals no damage.
   *
   * The advantage-granting rider is represented through the affected-combatant membership (isAffecting);
   * the threat value is a heuristic for the offensive benefit it provides to the caster's allies.
   */
  class FaerieFireFactory : public DirectThreatFactory
  {
    friend class FaerieFire;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::FEET_60;
    static constexpr SpellTarget target = SpellTarget::BOX_20;
    static constexpr Duration duration = Duration::MINUTE;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::HARMFUL;
    //! Heuristic threat value per enemy that would be outlined (grants advantage to attackers).
    static constexpr double THREAT_PER_TARGET = 3.0;

    FaerieFireFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource);

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
  };

  class FaerieFire : public Actoid, public LimitedDurationEffect, public AoeSquareEffect, public CombatantEffect, public DirectThreat
  {
  public:
    FaerieFire(const Coord &coord, const FaerieFireFactory &factory)
        : Effect(factory._combatant), // Explicitly construct the virtual base
          Actoid(const_cast<FaerieFireFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
          LimitedDurationEffect(factory._combatant, 100),
          AoeSquareEffect(factory._combatant, coord, TRANSLATE_BOX.at(FaerieFireFactory::target)),
          CombatantEffect(factory._combatant, {}), _coord(coord), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    EffectType getEffectType() const override { return EffectType::FAERIE_FIRE; }

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
    Coord _coord;
    const FaerieFireFactory &_factory;
  };
}
