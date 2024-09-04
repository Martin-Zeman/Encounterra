#pragma once

#include <vector>
#include <memory>
#include "core/interfaces.hpp"

namespace enc
{

  class Dodge : public Actoid
  {
  public:
    Dodge() : Actoid(ActoidFlags::IS_MOVEMENT) {}
  };

  class DodgeFactory : public ActoidFactory
  {
  public:
    std::vector<std::shared_ptr<Actoid>> createAll(void *previous_action_in_dag = nullptr) override { return {std::make_shared<Dodge>()}; }

    std::shared_ptr<Actoid> create(void *target) override { return std::make_shared<Dodge>(); }
  };

}
