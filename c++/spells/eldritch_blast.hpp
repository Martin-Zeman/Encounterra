#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  // Eldritch Blast (2024) — the warlock's signature Evocation cantrip. A ranged spell attack hurling a
  // beam of crackling energy at one creature for 1d10 Force damage. The cantrip creates additional beams as
  // the caster gains levels (two at 5, three at 11, four at 17); each beam is a separate attack roll and may
  // target the same or a different creature.
  //
  // Like Scorching Ray, the threat-maximising play concentrates every beam on a single target, so the
  // projected threat against that target equals the per-beam mean damage multiplied by the beam count.
  class EldritchBlastFactory : public DirectThreatFactory
  {
    friend class EldritchBlast;

  public:
    static constexpr int level = 0;
    static constexpr SpellRange range = SpellRange::FEET_120;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Force;
    static constexpr Die beamDmgDice = {1, 10};

    //! Number of beams by caster level (1 below 5, 2 at 5-10, 3 at 11-16, 4 at 17+).
    static constexpr int getNumBeams(int level)
    {
      if(level >= 17)
        {
          return 4;
        }
      if(level >= 11)
        {
          return 3;
        }
      if(level >= 5)
        {
          return 2;
        }
      return 1;
    }

    EldritchBlastFactory(int toHit, AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;

    std::optional<Resource *> getResource() override { return _resource; }

    //! Eldritch Invocation: Agonizing Blast adds the caster's spellcasting modifier to each beam's damage.
    void setAgonizingBlast(int dmgBonus) { _dmgBonus = dmgBonus; }
    int getDmgBonus() const { return _dmgBonus; }
    //! Eldritch Invocation: Repelling Blast pushes a hit target 10 ft straight away from the caster.
    void setRepellingBlast(bool repelling = true) { _repelling = repelling; }
    bool isRepelling() const { return _repelling; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    int _toHit;
    Resource *_resource;
    int _numBeams;
    int _dmgBonus = 0;
    bool _repelling = false;
  };

  class EldritchBlast : public Actoid, public DirectThreat
  {
  public:
    EldritchBlast(Combatant &target, const EldritchBlastFactory &factory, RollType rollType = RollType::STRAIGHT)
        : Actoid(const_cast<EldritchBlastFactory &>(factory), ActoidFlags::IS_SPELL | ActoidFlags::IS_ATTACK_LIKE, factory._abilityType),
          _target(target), _factory(factory), _rollType(rollType)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    Combatant &getTarget() const { return _target; }
    int getToHit() const { return _factory._toHit; }
    Die getDmgDice() const { return EldritchBlastFactory::beamDmgDice; }
    int getNumBeams() const { return _factory._numBeams; }
    int getDmgBonus() const { return _factory._dmgBonus; }
    bool isRepelling() const { return _factory._repelling; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Combatant &_target;
    const EldritchBlastFactory &_factory;
    RollType _rollType;
  };
}
