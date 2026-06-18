#pragma once

#include "core/interfaces.hpp"

namespace enc
{

  /**
   * Placeholder actoid carrying only a name and flags. Used to back the synthetic sentinel transitions
   * (e.g. "dummy"/"nop") that previously existed only as magic strings in the action DAG, so that every
   * transition has a value-identity backing actoid.
   */
  class DummyActoid : public Actoid
  {
  public:
    DummyActoid(ActoidFactory &factory, std::string name, ActoidFlags flags = ActoidFlags::DEFAULT)
        : Actoid(factory, flags), _name(std::move(name))
    {}

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
    std::size_t hash() const override
    {
      std::size_t h = std::hash<uint32_t>{}(_actoidFlags);
      h ^= std::hash<std::string>{}(_name) + 0x9e3779b9 + (h << 6) + (h >> 2);
      return h;
    }

  private:
    std::string _name;
  };

} // namespace enc
