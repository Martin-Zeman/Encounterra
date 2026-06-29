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

  // --- Description (Charm Person, 1st-level Enchantment) ---
  // Casting Time: Action | Range: 30 feet | Components: V, S | Duration: 1 hour
  // One Humanoid you can see within range makes a Wisdom saving throw, and it does so with Advantage if you or
  // your allies are fighting it. On a failed save, it is Charmed by you until the spell ends or until you or your
  // allies damage it. The Charmed target is friendly to you. At Higher Levels: target one additional Humanoid for
  // each spell slot level above 1.

  // Charm Person (2024): level 1 enchantment. One humanoid within 30 ft must succeed on a Wisdom save or be
  // Charmed for the duration. A charmed humanoid will not attack the caster's side, so we model the threat as
  // the offensive output we deny by taking it out of the fight, weighted by the chance it fails the save.
  class CharmPersonFactory : public DirectThreatFactory
  {
    friend class CharmPerson;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::FEET_30;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::TEN_MINUTES;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr SavingThrow savingThrow = SavingThrow::WIS;
    static constexpr int ROUND_HORIZON = 3;

    CharmPersonFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateMaxThreat() const override;

  private:
    int _dc;
    Resource *_resource;
  };

  class CharmPerson : public Actoid, public LimitedDurationEffect, public CombatantEffect, public DirectThreat
  {
  public:
    CharmPerson(Combatant &target, const CharmPersonFactory &factory)
        : Effect(factory._combatant), Actoid(const_cast<CharmPersonFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
          LimitedDurationEffect(factory._combatant, 10), CombatantEffect(factory._combatant, {&target}), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    EffectType getEffectType() const override { return EffectType::CHARM_PERSON; }

    double calculateThreat(const Kwargs &kwargs) override;

    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;

    int getDc() const { return _factory._dc; }

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    const CharmPersonFactory &_factory;
  };
}
