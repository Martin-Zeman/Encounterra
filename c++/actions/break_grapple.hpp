#pragma once

#include "core/interfaces.hpp"
#include "actions/action_types.hpp"
#include "core/conditions.hpp"
#include <memory>

namespace enc
{

  class BreakGrappleFactory : public ActoidFactory
  {
  public:
    explicit BreakGrappleFactory(std::weak_ptr<ConditionWithDC> grappleCondition);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override 
    { 
      return {create(nullptr)}; 
    }

    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return {}; }

  private:
    std::weak_ptr<ConditionWithDC> _grappleCondition;
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

    bool equals(const Actoid &other) const override { return true;}

  protected:
    size_t hash() const override { return 0;}
  };

} // namespace enc
