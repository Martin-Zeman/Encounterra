#pragma once

#include "core/interfaces.hpp"
#include "core/misc.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/combatant_effect.hpp"
#include "effects/limited_duration_effect.hpp"
#include "spells/spell_stats.hpp"

namespace enc
{
  class Combatant;

  // --- Description (Hex, 1st-level Enchantment) ---
  // Casting Time: Bonus Action | Range: 90 feet | Components: V, S, M (the petrified eye of a newt)
  // Duration: Concentration, up to 1 hour
  // You place a curse on a creature you can see within range. Until the spell ends you deal an extra 1d6
  // Necrotic damage to the target whenever you hit it with an attack roll. You also choose one ability when
  // you cast the spell; the target has Disadvantage on ability checks made with that ability. If the target
  // drops to 0 Hit Points before the spell ends, you can use a Bonus Action on a later turn to curse a new
  // creature.
  //
  // Modelled as a self-buff that empowers the caster's own attacks against the hexed target, mirroring Vow of
  // Enmity but contributing a flat +1d6 Necrotic damage die (via DMG_BONUS_DIE) rather than advantage. The
  // bonus applies to BOTH weapon attacks and spell attacks (e.g. Eldritch Blast), so the delta is taken from
  // whichever DirectThreat attack is aimed at the hexed creature.
  class HexFactory : public ThreatModifierFactory
  {
    friend class Hex;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::FEET_90;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::MINUTE;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr int durationRounds = 10;
    static constexpr Die extraDmgDice = {1, 6};
    static constexpr DamageType dmgType = DamageType::Necrotic;

    HexFactory(AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;

  private:
    Resource *_resource;
  };

  class Hex : public AttackThreatModifier, public CombatantEffect, public LimitedDurationEffect
  {
  public:
    Hex(Combatant &target, HexFactory &factory);

    EffectType getEffectType() const override { return EffectType::HEX; }
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;

    std::string toString() const override;
    std::string shorthandStr() const;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) override;

  private:
    HexFactory &_factory;
  };
}
