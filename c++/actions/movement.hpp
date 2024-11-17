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

    operator std::string() const { return "(" + std::to_string(_increment[0]) + "," + std::to_string(_increment[1]) + ")"; }
    const Coord &getIncrement() const { return _increment; }
    bool incursAOO() const { return _incursAOO; }

  private:
    Coord _increment;
    bool _incursAOO;
  };

  class MovementFactory : public ActoidFactory
  {
  public:
    static const std::unordered_map<AbilityType, std::string> MOVEMENT_TYPE_NAMES;

    MovementFactory(Combatant *combatant, std::vector<Coord> path, AbilityType movementType = AbilityType::STANDARD_MOVEMENT);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return {}; }

    // void setPath(const std::vector<Coord> &path) { _path = path; }

  private:
    std::vector<Coord> _path;
  };

  class GetUpFactory : public ActoidFactory
  {
    friend class GetUpFromProne; // Allow GetUpFromProne to access private members of GetUpFactory
  public:
    GetUpFactory(Combatant *combatant) : ActoidFactory("Get Up Factory", "Get Up", combatant, AbilityType::GET_UP_FROM_PRONE) {}

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override { return {create(nullptr)}; }

    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return {}; }
  };

  class GetUpFromProne : public Actoid
  {
  public:
    explicit GetUpFromProne(ActoidFactory &factory) : Actoid(factory, ActoidFlags::IS_GET_UP_FROM_PRONE) {}

    operator std::string() const { return "Get Up from Prone"; }
    std::string shorthandStr() const { return "Get Up from Prone"; }
  };
}
