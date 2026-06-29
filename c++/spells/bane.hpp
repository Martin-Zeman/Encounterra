#pragma once

#include "spells/spell_stats.hpp"
#include "core/interfaces.hpp"
#include "core/misc.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/combatant_effect.hpp"
#include "effects/limited_duration_effect.hpp"

namespace enc
{
  class Combatant;

  // --- Description (Bane, 1st-level Enchantment) ---
  // Casting Time: Action | Range: 30 feet | Components: V, S, M (a drop of blood) | Duration: Concentration, up to 1 minute
  // Up to three creatures of your choice that you can see within range must each make a Charisma saving throw.
  // Whenever a target that fails this save makes an attack roll or a saving throw before the spell ends, the
  // target must subtract 1d4 from the attack roll or save. At Higher Levels: target one additional creature for
  // each spell slot level above 1.

  // Bane (2024): level 1 enchantment, the mirror image of Bless. Up to three creatures within 30 ft make a
  // Charisma save; while the spell lasts a target that failed subtracts 1d4 from its attack rolls and saving
  // throws. Concentration, up to 1 minute. Threat is the offensive output we deny the affected enemies.
  class BaneFactory : public ThreatModifierFactory
  {
    friend class Bane;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::FEET_30;
    static constexpr SpellTarget target = SpellTarget::THREE_CREATURES;
    static constexpr Duration duration = Duration::MINUTE;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr SavingThrow savingThrow = SavingThrow::CHA;
    static constexpr double ROUND_HORIZON = 3.0;

    BaneFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<std::vector<Combatant *>> getEligibleTargetGroups() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;

  private:
    int _dc;
    Resource *_resource;
  };

  class Bane : public AttackThreatModifier, public CombatantEffect, public LimitedDurationEffect
  {
  public:
    static constexpr Die penaltyDie{1, 4};

    Bane(std::vector<Combatant *> targets, BaneFactory &factory);

    EffectType getEffectType() const override { return EffectType::BANE; }
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;

    std::string toString() const override;
    std::string shorthandStr() const;

    double calculateThreat(const Kwargs &kwargs) override;
    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

    int getDc() const { return _factory._dc; }

  private:
    void applyPenalties(Combatant *combatant);
    void removePenalties(Combatant *combatant);

    BaneFactory &_factory;
  };
}
