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
    explicit BreakGrappleFactory(Combatant *combatant);

    std::vector<Actoid *> createAll(void *previousActionInDag = nullptr) override
    {
      return {}; // Can't create without knowing the condition
    }

    Actoid *create(void *target) override;

    std::optional<Resource *> getResource() override { return {}; }
  };

  class BreakGrapple : public Actoid
  {
  public:
    BreakGrapple(BreakGrappleFactory &factory, ConditionWithDC *grappleCondition);

    BreakGrapple(const BreakGrapple &other);

    Actoid *clone() const override { return new BreakGrapple(*this); }

    std::string toString() const override { return "Break Grapple"; }
    std::string shorthandStr() const { return "Break Grapple"; }

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override
    {
      return std::nullopt;
    }

    bool equals(const Actoid &other) const override
    {
      if(auto *breakGrapple = dynamic_cast<const BreakGrapple *>(&other))
        {
          return _grappleCondition == breakGrapple->_grappleCondition;
        }
      return false;
    }

  protected:
    size_t hash() const override { return std::hash<ConditionWithDC *>{}(_grappleCondition); }

  private:
    ConditionWithDC *_grappleCondition;
  };
} // namespace enc
