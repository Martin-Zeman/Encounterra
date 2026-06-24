#pragma once

#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  // Innate Sorcery (2024) — a bonus action, usable twice per long rest. For 1 minute the sorcerer's
  // spell save DC increases by 1 and they have advantage on the attack rolls of their sorcerer spells.
  //
  // Modeled as a self-targeting ThreatModifierFactory (mirroring Python's RageFactory): the threat it
  // generates equals the improvement the advantage grants to the caster's own spell attacks, projected
  // over the spell's duration, so the planner has a reason to cast it. The +1 save DC rider is not
  // modeled (the engine stores DC as a fixed integer).
  class InnateSorceryFactory : public ThreatModifierFactory
  {
    friend class InnateSorcery;

  public:
    static constexpr int dcBonus = 1;
    static constexpr int maxUses = 2;

    InnateSorceryFactory(Combatant *caster, Resource *resource);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;

    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateMaxThreat() const;

  private:
    Resource *_resource;
  };

  // Modeled as an AttackThreatModifier (mirroring Rage): the buff carries no inherent threat of its own;
  // instead, when it precedes a sorcerer spell attack in a planned sequence it contributes that attack's
  // advantage delta via calculateThreatForAttack. This makes the branch of the game tree in which Innate
  // Sorcery is channeled BEFORE the spell score highest, so the planner orders it first. The benefit is
  // conditioned on the buff not being active yet — once active it grants no further advantage, so its threat
  // is zero and it is not re-channeled.
  class InnateSorcery : public AttackThreatModifier
  {
  public:
    InnateSorcery(const InnateSorceryFactory &factory)
        : AttackThreatModifier(const_cast<InnateSorceryFactory &>(factory), ActoidFlags::IS_SPELL, AbilityType::INNATE_SORCERY),
          _factory(factory)
    {}

    std::string toString() const override { return "Innate Sorcery"; }

    std::string shorthandStr() const { return "Innate Sorcery"; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) override;
    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    const InnateSorceryFactory &_factory;
  };
}
