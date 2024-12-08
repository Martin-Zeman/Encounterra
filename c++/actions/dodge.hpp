#pragma once

#include <vector>
#include <memory>
#include "core/interfaces.hpp"

namespace enc
{

  class DodgeFactory : public ActoidFactory
  {
    friend class Dodge;

  public:
    DodgeFactory(Combatant *combatant) : ActoidFactory("DodgeFactory", "Dodge", combatant, AbilityType::DODGE) {}

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;

    std::optional<Resource *> getResource() override { return {}; }
  };

  class Dodge : public Actoid
  {
  public:
    Dodge(ActoidFactory &factory) : Actoid(factory, ActoidFlags::IS_MOVEMENT, AbilityType::DODGE) {}

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                        const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;
  };

}
