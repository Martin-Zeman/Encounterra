#pragma once

#include <memory>
#include <vector>
#include "core/types.hpp"
#include "core/interfaces.hpp"

namespace enc
{

  class Combatant;

  class ActionPlanStrategy
  {
  public:
    explicit ActionPlanStrategy(Combatant *combatant) : _combatant(combatant) {}
    virtual ~ActionPlanStrategy() = default;

    virtual std::vector<std::shared_ptr<Actoid>>
    calculateActionPlan(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths) = 0;

  protected:
    Combatant *_combatant;
  };

} // namespace enc
