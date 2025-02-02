#pragma once

#include <vector>
#include <memory>
#include "core/interfaces.hpp"

namespace enc
{
  class DisengageFactory : public ActoidFactory
  {
    friend class Disengage;

  public:
    DisengageFactory(Combatant *combatant, AbilityType abilityType = AbilityType::DISENGAGE) : ActoidFactory("DisengageFactory", "Disengage", combatant, abilityType) {}

    std::vector<Actoid *> createAll(void *previousActionInDag = nullptr) override;

    Actoid * create(void *target) override;

    std::optional<Resource *> getResource() override { return {}; }
  };

  class Disengage : public Actoid
  {
  public:
    Disengage(ActoidFactory &factory) : Actoid(factory, ActoidFlags::LOCATION_INDEPENDENT | ActoidFlags::LOCATION_INDEPENDENT, factory.getAbilityType()) {}

    Disengage(const Disengage &other)
        : Actoid(const_cast<ActoidFactory &>(other._factory), static_cast<ActoidFlags>(other._actoidFlags), other._abilityType)
    {}

    Actoid *clone() const override { return new Disengage(*this); }

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;
    std::string toString() const override;
    bool equals(const Actoid &other) const override;

  protected:
    size_t hash() const override;
  };
}
