// action_plan_strategy.hpp
#pragma once
#include <memory>
#include <vector>
#include "actions/action_plan_strategy.hpp"
#include "core/types.hpp"
#include "core/interfaces.hpp"

namespace enc
{

  class Combatant;

  class DefaultActionPlanStrategy : public ActionPlanStrategy
  {
  public:
    explicit DefaultActionPlanStrategy(Combatant &combatant) : ActionPlanStrategy(combatant) {}

    std::vector<std::shared_ptr<Actoid>>
    calculateActionPlan(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths) override;

  private:
    std::pair<std::vector<std::shared_ptr<Actoid>>, std::array<double, 2>>
    getMovementAndThreatForNextTurn(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths,
                                    double infeasibilityMultiplier = 0.5);

    std::vector<std::shared_ptr<Actoid>> extractMovement(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths,
                                                         const std::vector<std::shared_ptr<Actoid>> &sequence);
  };

} // namespace enc