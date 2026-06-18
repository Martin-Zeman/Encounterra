#pragma once

#include "core/interfaces.hpp"
#include "actions/dummy_actoid.hpp"

namespace enc
{

  /**
   * Trivial factory used as the owning factory for DummyActoid sentinels. It does not produce actoids through the
   * normal createAll()/create() pipeline; callers construct DummyActoid instances directly using this factory as
   * their (non-owning) factory reference. A process-wide singleton is provided since the factory is stateless.
   */
  class DummyActoidFactory : public ActoidFactory
  {
  public:
    static DummyActoidFactory &getInstance()
    {
      static DummyActoidFactory instance;
      return instance;
    }

    DummyActoidFactory(const DummyActoidFactory &) = delete;
    DummyActoidFactory &operator=(const DummyActoidFactory &) = delete;

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override { return {}; }
    std::shared_ptr<Actoid> create(void *target) override { return nullptr; }
    std::optional<Resource *> getResource() override { return std::nullopt; }

  private:
    DummyActoidFactory() : ActoidFactory("Dummy Factory", "Dummy", nullptr, AbilityType::NOP) {}
  };

} // namespace enc
