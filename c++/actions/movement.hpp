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

    bool equals(const Actoid &other) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &coords = blaze::DynamicMatrix<Coord>()) override;

    std::string toString() const override;

  protected:
    size_t hash() const override;

  private:
    Coord _increment;
    bool _incursAOO;
  };

  class MovementFactory : public ActoidFactory
  {
  public:
    static const std::unordered_map<AbilityType, std::string> MOVEMENT_TYPE_NAMES;

    MovementFactory(Combatant *combatant, CoordVector path, AbilityType movementType = AbilityType::STANDARD_MOVEMENT);

    std::vector<Actoid *> createAll(void *previousActionInDag = nullptr) override;
    Actoid * create(void *target) override;
    std::optional<Resource *> getResource() override { return {}; }

    // void setPath(const CoordVector &path) { _path = path; }

  private:
    CoordVector _path;
  };

  class GetUpFactory : public ActoidFactory
  {
    friend class GetUpFromProne; // Allow GetUpFromProne to access private members of GetUpFactory
  public:
    GetUpFactory(Combatant *combatant) : ActoidFactory("Get Up Factory", "Get Up", combatant, AbilityType::GET_UP_FROM_PRONE) {}

    std::vector<Actoid *> createAll(void *previousActionInDag = nullptr) override { return {create(nullptr)}; }

    Actoid *create(void *target) override;
    std::optional<Resource *> getResource() override { return {}; }
  };

  class GetUpFromProne : public Actoid
  {
  public:
    explicit GetUpFromProne(ActoidFactory &factory) : Actoid(factory, ActoidFlags::IS_MOVEMENT) {}

    operator std::string() const { return "Get Up from Prone"; }
    std::string shorthandStr() const { return "Get Up from Prone"; }
    bool equals(const Actoid &other) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &coords = blaze::DynamicMatrix<Coord>()) override;

    std::string toString() const override;

  protected:
    size_t hash() const override;
  };
}
