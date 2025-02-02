#pragma once

#include "core/interfaces.hpp"

namespace enc
{

  class DummyActoid : public Actoid
  {
  public:
    DummyActoid(ActoidFactory &factory, std::string name, ActoidFlags flags = ActoidFlags::DEFAULT) : Actoid(factory, flags), _name(std::move(name))
    {}

    DummyActoid(const DummyActoid &other) : Actoid(other._factory, static_cast<ActoidFlags>(other._actoidFlags), other._abilityType), _name(other._name) {}

    Actoid *clone() const override { return new DummyActoid(*this); }

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override
    {
      return std::nullopt;
    }

    std::string toString() const override { return _name; }

    bool equals(const Actoid &other) const override
    {
      if(auto *o = dynamic_cast<const DummyActoid *>(&other))
        {
          return _name == o->_name && _actoidFlags == o->_actoidFlags;
        }
      return false;
    }

  protected:
    size_t hash() const override
    {
      size_t h = std::hash<uint32_t>{}(_actoidFlags);
      h ^= std::hash<std::string>{}(_name) + 0x9e3779b9 + (h << 6) + (h >> 2);
      return h;
    }

  private:
    std::string _name;
  };
}
