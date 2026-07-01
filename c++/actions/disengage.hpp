#pragma once

#include <vector>
#include <memory>
#include "core/interfaces.hpp"

namespace enc
{
  class DisengageFactory : public ActoidFactory
  {
    friend class Disengage;

  public:
    DisengageFactory(Combatant *combatant, AbilityType abilityType = AbilityType::DISENGAGE)
        : ActoidFactory("DisengageFactory", "Disengage", combatant, abilityType)
    {}

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;

    std::optional<Resource *> getResource() override { return {}; }
  };

  class Disengage : public Actoid
  {
  public:
    Disengage(ActoidFactory &factory)
        : Actoid(factory, ActoidFlags::LOCATION_INDEPENDENT | ActoidFlags::IS_PRIORITY, factory.getAbilityType())
    {}

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;
    std::string toString() const override;
  };
}
