#pragma once

#include "core/interfaces.hpp"
#include "actions/action_types.hpp"
#include "core/conditions.hpp"

namespace enc
{

  class BreakGrappleFactory : public ActoidFactory
  {
  public:
    explicit BreakGrappleFactory(Condition *grappleCondition);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override { return {create(nullptr)}; }

    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return {}; }

  private:
    Condition *_grappleCondition;
  };

  class BreakGrapple : public Actoid
  {
  public:
    explicit BreakGrapple(BreakGrappleFactory &factory);

    std::string toString() const override { return "Break Grapple"; }
    std::string shorthandStr() const { return "Break Grapple"; }

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override
    {
      return std::nullopt;
    }
  };

} // namespace enc
