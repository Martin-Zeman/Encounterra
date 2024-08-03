#pragma once

#include <vector>
#include <memory>
#include "core/interfaces.hpp"

namespace enc
{

  class Disengage : public Actoid
  {
  public:
    Disengage() : Actoid(ActoidFlags::IS_MOVEMENT) {}
  };

  class DisengageFactory : public Factory
  {
  public:
    std::vector<std::shared_ptr<Actoid>> create_all(void *previous_action_in_dag = nullptr) override { return {std::make_shared<Disengage>()}; }

    std::shared_ptr<Actoid> create(void *target) override { return std::make_shared<Disengage>(); }
  };
}