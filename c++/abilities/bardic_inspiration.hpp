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

  // --- Description (Bardic Inspiration, Bard level 1 feature) ---
  // You can supernaturally inspire others through words, music, or dance. As a Bonus Action, you give one creature
  // (other than yourself) within 60 feet a Bardic Inspiration die (a d6). Once within the next hour, the creature
  // can roll the die and add the number rolled to one ability check, attack roll, or saving throw. You can use
  // this feature a number of times equal to your Charisma modifier (minimum once), regaining all uses on a long
  // rest. The die grows with bard level (d8 at 5th, d10 at 10th, d12 at 15th).

  // Bardic Inspiration (2024): bonus action, a number of uses equal to the bard's Charisma modifier per long
  // rest. The bard gives one ally within 60 ft a Bardic Inspiration die (d6 at levels 1-4) that the ally adds
  // to one attack roll or saving throw. Modeled like a single-target Bless: a +1d6 to-hit / saving-throw
  // bonus held by one ally, registered as a bonus action drawing from the shared inspiration pool.
  class BardicInspirationFactory : public ThreatModifierFactory
  {
    friend class BardicInspiration;

  public:
    static constexpr SpellRange range = SpellRange::FEET_60;
    static constexpr Die inspirationDie{1, 6};
    static constexpr double SAVING_THROW_BONUS_MULTIPLIER = 1.25;

    static int getUses(int chaModifier) { return chaModifier > 0 ? chaModifier : 1; }

    BardicInspirationFactory(AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;

  private:
    Resource *_resource;
  };

  class BardicInspiration : public AttackThreatModifier, public CombatantEffect, public LimitedDurationEffect
  {
  public:
    BardicInspiration(Combatant &target, BardicInspirationFactory &factory);

    EffectType getEffectType() const override { return EffectType::BARDIC_INSPIRATION; }
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;

    std::string toString() const override;
    std::string shorthandStr() const;

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) override;
    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    BardicInspirationFactory &_factory;
  };
}
