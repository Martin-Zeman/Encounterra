#pragma once

#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  /**
   * Second Wind (2024 Fighter, level 1): as a Bonus Action the fighter regains 1d10 + Fighter level hit
   * points. It has a limited number of uses (refreshed on a Short or Long Rest). Modelled as a self-targeting
   * DirectThreat (mirroring the Python abilities/second_wind.py) whose "threat" is the capped amount of
   * missing hit points it can restore, so the planner values it like a beneficial bonus action.
   */
  class SecondWindFactory : public DirectThreatFactory
  {
    friend class SecondWind;

  public:
    SecondWindFactory(Combatant *combatant, Resource *resource, int level, Die healDice = Die{1, 10});

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateMaxThreat() const override;

  protected:
    Resource *_resource;
    int _level;
    Die _healDice;
  };

  class SecondWind : public Actoid, public DirectThreat
  {
  public:
    SecondWind(Combatant &target, const SecondWindFactory &factory)
        : Actoid(const_cast<SecondWindFactory &>(factory), ActoidFlags::LOCATION_INDEPENDENT, AbilityType::SECOND_WIND), _target(target),
          _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    Combatant &getTarget() const { return _target; }
    int getMod() const { return _factory._level; }
    Die getHealDice() const { return _factory._healDice; }

    double calculateThreat(const Kwargs &kwargs) override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Combatant &_target;
    const SecondWindFactory &_factory;
  };
}
