#pragma once

#include <vector>
#include <memory>
#include "core/interfaces.hpp"

namespace enc
{

  class Disengage : public Actoid
  {
  public:
    Disengage(ActoidFactory& factory) : Actoid(factory, ActoidFlags::IS_MOVEMENT, AbilityType::DISENGAGE) {}
    
  };

  class DisengageFactory : public ActoidFactory
  {
  public:
    std::vector<std::shared_ptr<Actoid>> createAll(void *previous_action_in_dag = nullptr) override { return {std::make_shared<Disengage>(*this)}; }

    std::shared_ptr<Actoid> create(void *target) override { return std::make_shared<Disengage>(*this); }

    std::optional<Resource *> getResource() override { return {};}
  };
}