#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  // Shield (2024) — a level 1 reaction granting +5 AC until the start of the caster's next turn.
  // Modeled as a zero-threat self buff; the AC bonus is applied through the caster's one-time
  // shield-AC bonus when the reaction is resolved.
  class ShieldFactory : public ActoidFactory
  {
    friend class Shield;

  public:
    static constexpr int level = 1;
    static constexpr int acBonus = 5;
    static constexpr SpellRange range = SpellRange::SELF;
    static constexpr SpellTarget target = SpellTarget::SELF;
    static constexpr Duration duration = Duration::ROUND_ONE;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::BUFF;

    ShieldFactory(Combatant *caster, Resource *resource)
        : ActoidFactory("ShieldFactory", "Shield", caster, AbilityType::SHIELD), _resource(resource)
    {}

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;

    std::optional<Resource *> getResource() override { return _resource; }

  private:
    Resource *_resource;
  };

  class Shield : public Actoid, public Threat
  {
  public:
    Shield(const ShieldFactory &factory)
        : Actoid(const_cast<ShieldFactory &>(factory), ActoidFlags::IS_SPELL, AbilityType::SHIELD), _factory(factory)
    {}

    std::string toString() const override { return "Shield"; }

    std::string shorthandStr() const { return "Shield"; }

    double calculateThreat(const Kwargs &kwargs) override;
    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    const ShieldFactory &_factory;
  };
}
