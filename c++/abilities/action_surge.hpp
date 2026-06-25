#pragma once

#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  /**
   * Action Surge (2024 Fighter, level 2): once per Short or Long Rest the fighter may take one additional
   * Action on its turn. It is a Free Action gated only by its limited-use resource. The extra Action is
   * surfaced to the planner via the action-enabler mechanism: the ActionSurge actoid carries the
   * IS_ACTION_ENABLER flag and useResources restores the fighter's Action, so the proto-DAG recurses with a
   * fresh Action available (mirroring the Python abilities/action_surge.py + ActionSurgePlanStrategy).
   */
  class ActionSurgeFactory : public DirectThreatFactory
  {
    friend class ActionSurge;

  public:
    ActionSurgeFactory(Combatant *combatant, Resource *resource);

    //! Number of Action Surge uses by Fighter level (1 at levels 1-16, 2 at 17-20).
    static int getActionSurgeUses(int level);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateMaxThreat() const override;

  protected:
    Resource *_resource;
  };

  class ActionSurge : public Actoid, public DirectThreat
  {
  public:
    explicit ActionSurge(const ActionSurgeFactory &factory)
        : Actoid(const_cast<ActionSurgeFactory &>(factory), ActoidFlags::IS_ACTION_ENABLER | ActoidFlags::LOCATION_INDEPENDENT,
                 AbilityType::ACTION_SURGE),
          _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    double calculateThreat(const Kwargs &kwargs) override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    const ActionSurgeFactory &_factory;
  };
}
