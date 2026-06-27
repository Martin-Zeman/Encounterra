#pragma once

#include <memory>
#include <optional>
#include <string>
#include <blaze/Math.h>
#include "core/interfaces.hpp"
#include "core/conditions.hpp"

namespace enc
{
  /**
   * Action representing an attempt to break out of a grapple.
   * Mirrors Python simulator/actions/break_grapple.py (BreakGrapple / BreakGrappleFactory).
   */
  class BreakGrappleFactory : public ActoidFactory
  {
  public:
    explicit BreakGrappleFactory(const ConditionWithDC &grappleCondition, Combatant *combatant = nullptr)
        : ActoidFactory("Break Grapple Factory", "Break Grapple", combatant, AbilityType::BREAK_GRAPPLE), _grappleCondition(grappleCondition)
    {
      setFlag(FactoryFlags::DEFAULT);
    }

    const ConditionWithDC &getGrappleCondition() const { return _grappleCondition; }

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override { return {create(nullptr)}; }
    std::shared_ptr<Actoid> create(void *target = nullptr) override;
    std::optional<Resource *> getResource() override { return {}; }

  private:
    ConditionWithDC _grappleCondition;
  };

  class BreakGrapple : public Actoid
  {
  public:
    explicit BreakGrapple(ActoidFactory &factory) : Actoid(factory, ActoidFlags::IS_BREAK_GRAPPLE) {}

    AbilityType getAbilityType() const override { return AbilityType::BREAK_GRAPPLE; }
    std::string shorthandStr() const { return "Break Grapple"; }

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override
    {
      return {};
    }
    std::string toString() const override { return "Break Grapple"; }
  };
}
