#pragma once

#include <optional>
#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  class MistyStepFactory : public ActoidFactory
  {
    friend class MistyStep; // Allow MistyStep to access private members of MistyStepFactory

  public:
    static constexpr int level = 2;
    static constexpr SpellRange range = SpellRange::FEET_30;
    static constexpr SpellTarget target = SpellTarget::SELF;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::OTHER;

    MistyStepFactory(const std::shared_ptr<Combatant> &caster, Resource *resource);

    std::optional<Coord> getEligibleTargets() const;

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;

    std::optional<Resource *> getResource() override { return _resource; }

  private:
    Resource *_resource;
  };

  class MistyStep : public Actoid
  {
  public:
    MistyStep(const Coord &coord, const MistyStepFactory &factory);

    ~MistyStep() override;

    std::string toString() const override { return "MistyStep to (" + std::to_string(_coord[0]) + ", " + std::to_string(_coord[1]) + ")"; }

    std::string shorthandStr() const { return "MistyStep"; }

    double calculateThreat(const Kwargs &kwargs) override;
    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;
    bool equals(const Actoid &other) const override;

  protected:
    size_t hash() const override;

  private:
    Coord _coord;
    const MistyStepFactory &_factory;
  };
} // namespace enc
