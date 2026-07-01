#pragma once

#include "core/interfaces.hpp"
#include "core/types.hpp"
#include "actions/action_types.hpp"
#include "effects/combatant_effect.hpp"
#include <memory>
#include <vector>

namespace enc
{
  class Combatant;

  /**
   * Hide (2024). Offered per enemy the rogue is not already Hidden from. Modelled as a ThreatModifierFactory
   * (mirroring Python actions/hide.HideFactory): it does NOT set IS_DIRECT_THREAT, so it does not recurse into
   * the threat-delta loops of other modifiers. The threat it grants is the Advantage (and, for a rogue, the
   * Sneak Attack) its Hidden condition would enable on the rogue's next attack against that enemy.
   *
   * The geometry of "where can I stand such that this enemy cannot see me" is unchanged from the existing
   * visibility machinery (BattleMap::getVisibilityDictForAllCoords / Visibility::NONE).
   */
  class HideFactory : public ThreatModifierFactory
  {
    friend class Hide;

  public:
    HideFactory(Combatant *combatant, AbilityType abilityType = AbilityType::HIDE)
        : ThreatModifierFactory("HideFactory", "Hide", combatant, abilityType)
    {}

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return {}; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override { return 0.0; }
  };

  class Hide : public AttackThreatModifier, public CombatantEffect
  {
  public:
    Hide(HideFactory &factory, Combatant *target);

    EffectType getEffectType() const override;
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;

    std::string toString() const override;
    std::string shorthandStr() const;

    Combatant *getTarget() const { return _target; }

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

    double calculateThreat(const Kwargs &kwargs) override { return 0.0; }
    double calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) override;

  private:
    //! "Cunning " for CUNNING_HIDE, "Hasted " for HASTE_HIDE, empty otherwise (mirrors the Python prefixes).
    std::string prefix() const;

    HideFactory &_factory;
  };
}
