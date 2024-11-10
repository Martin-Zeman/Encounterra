#pragma once

#include "core/types.hpp"
#include "core/interfaces.hpp"
#include <vector>
#include <memory>

namespace enc
{
  class MovementIncrement : public Actoid
  {
  public:
    MovementIncrement(const Coord &increment, bool incursAOO, ActoidFactory &factory)
        : Actoid(factory, ActoidFlags::IS_MOVEMENT), _increment(increment), _incursAOO(incursAOO)
    {}

    std::string toString() const override { return "(" + std::to_string(_increment[0]) + "," + std::to_string(_increment[1]) + ")"; }
    const Coord &getIncrement() const { return _increment; }
    bool incursAOO() const { return _incursAOO; }

  private:
    Coord _increment;
    bool _incursAOO;
  };

  class MovementFactory : public ActoidFactory
  {
  public:
    MovementFactory(Combatant *combatant, std::vector<Coord> path, AbilityType movementType = AbilityType::STANDARD_MOVEMENT)
        : ActoidFactory("Movement", combatant, movementType), _path(path)
    {}

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return {}; }

    // void setPath(const std::vector<Coord> &path) { _path = path; }

  private:
    std::vector<Coord> _path;
  };

  class GetUpFactory : public ActoidFactory
  {
  public:
    GetUpFactory(Combatant *combatant) : ActoidFactory("Get Up", combatant, AbilityType::GET_UP_FROM_PRONE) {}

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override { return {create(nullptr)}; }

    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return {}; }
  };

  class GetUpFromProne : public Actoid
  {
  public:
    explicit GetUpFromProne(ActoidFactory &factory) : Actoid(factory, ActoidFlags::IS_GET_UP_FROM_PRONE) {}

    std::string toString() const override { return "Get Up from Prone"; }
    std::string shorthandStr() const { return "Get Up from Prone"; }
  };
}
