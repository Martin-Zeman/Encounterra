#pragma once

#include "core/interfaces.hpp"

namespace enc
{
  class TestActoid : public Actoid
  {
  public:
    TestActoid(ActoidFactory &factory, std::string name, ActoidFlags flags = ActoidFlags::DEFAULT) : Actoid(factory, flags), _name(std::move(name)) {}

    TestActoid(const TestActoid &other)
        : Actoid(const_cast<ActoidFactory &>(other._factory), static_cast<ActoidFlags>(other._actoidFlags), other._abilityType),
          _name(other._name)
    {}

    Actoid *clone() const override { return new TestActoid(*this); }

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override
    {
      return std::nullopt;
    }

    std::string toString() const override { return _name; }
    bool equals(const Actoid &other) const override
    {
      if(auto *o = dynamic_cast<const TestActoid *>(&other))
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

  class TestActoidFactory : public ActoidFactory
  {
  public:
    TestActoidFactory() : ActoidFactory("TestFactory", "Test", nullptr, AbilityType::NOP) {}

    std::vector<Actoid *> createAll(void *previousActionInDag = nullptr) override { return {}; }

    Actoid * create(void *target) override { return nullptr; }

    std::optional<Resource *> getResource() override { return std::nullopt; }

    Actoid *createTestActoid(const std::string &name) { return new TestActoid(*this, name); }
  };
} // namespace enc
