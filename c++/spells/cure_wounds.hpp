#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  /**
   * Cure Wounds (2024): level 1, range Touch, action, instantaneous. Heals one creature for 2d8 + the
   * caster's spellcasting modifier. Like Healing Word but an action, touch range and a bigger heal die.
   */
  class CureWoundsFactory : public DirectThreatFactory
  {
    friend class CureWounds;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::TOUCH;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::BUFF;

    CureWoundsFactory(Combatant *caster, Resource *resource, int mod, AbilityType abilityType = AbilityType::CURE_WOUNDS,
                      Die healDice = Die{2, 8});

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  protected:
    Resource *_resource;
    int _mod;
    Die _healDice;
  };

  class CureWounds : public Actoid, public DirectThreat
  {
  public:
    CureWounds(Combatant &target, const CureWoundsFactory &factory)
        : Actoid(const_cast<CureWoundsFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType), _target(target), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    Combatant &getTarget() const { return _target; }
    int getMod() const { return _factory._mod; }
    Die getHealDice() const { return _factory._healDice; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Combatant &_target;
    const CureWoundsFactory &_factory;
  };
}
