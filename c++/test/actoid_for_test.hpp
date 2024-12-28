#pragma once

#include "core/interfaces.hpp"

namespace enc
{
  class TestActoid : public Actoid
  {
  public:
    TestActoid(ActoidFactory &factory, std::string name, ActoidFlags flags = ActoidFlags::DEFAULT) : Actoid(factory, flags), _name(std::move(name)) {}

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

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override { return {}; }

    std::shared_ptr<Actoid> create(void *target) override { return nullptr; }

    std::optional<Resource *> getResource() override { return std::nullopt; }

    std::shared_ptr<TestActoid> createTestActoid(const std::string &name) { return std::make_shared<TestActoid>(*this, name); }
  };
} // namespace enc
