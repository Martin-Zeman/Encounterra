#pragma once

#include "core/interfaces.hpp"
#include "actions/dummy_actoid.hpp"

namespace enc
{

  class DummyActoidFactory : public ActoidFactory
  {
  public:
    static DummyActoidFactory &getInstance()
    {
      static DummyActoidFactory instance;
      return instance;
    }

    // Delete copy constructor and assignment
    DummyActoidFactory(const DummyActoidFactory &) = delete;
    DummyActoidFactory &operator=(const DummyActoidFactory &) = delete;

    std::vector<Actoid *> createAll(void *previousActionInDag = nullptr) override { return {}; }

    Actoid *create(void *target) override { return nullptr; }

    std::optional<Resource *> getResource() override { return std::nullopt; }

    DummyActoid *createTestActoid(const std::string &name) { return new DummyActoid(*this, name); }

  private:
    DummyActoidFactory() : ActoidFactory("DummyFactory", "Dummy", nullptr, AbilityType::NOP) {}
  };

} // namespace enc
