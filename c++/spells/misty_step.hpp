#pragma once

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

    MistyStepFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
        : ActoidFactory("MistyStepFactory", "MistyStep", caster, abilityType), _resource(resource)
    {}

    std::string getAbilityName() const { return "MistyStep"; }

    Coord findBestArgs() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;

    std::optional<Resource *> getResource() override { return _resource; }

  private:
    Resource *_resource;
  };

  class MistyStep : public Actoid, public Threat
  {
  public:
    MistyStep(const Coord &coord, const MistyStepFactory &factory)
        : Actoid(const_cast<MistyStepFactory &>(factory), ActoidFlags::IS_SPELL, AbilityType::MISTY_STEP), _coord(coord), _factory(factory)
    {}

    std::string toString() const { return "MistyStep to (" + std::to_string(_coord[0]) + ", " + std::to_string(_coord[1]) + ")"; }

    std::string shorthandStr() const { return "MistyStep"; }

    double calculateThreat(const Kwargs &kwargs) override;
    std::optional<std::vector<Coord>> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                        const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Coord _coord;
    const MistyStepFactory &_factory;
  };
}