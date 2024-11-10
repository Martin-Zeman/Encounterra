#pragma once

#include "abilities/wildshape.hpp"
#include "actions/action_types.hpp"
// #include "combatants/brown_bear.hpp"
// #include "combatants/dire_wolf.hpp"
// #include "combatants/giant_constrictor_snake.hpp"
// #include "combatants/giant_spider.hpp"
// #include "combatants/giant_toad.hpp"
// #include "combatants/quetzalcoatlus.hpp"
// #include "combatants/saber_toothed_tiger.hpp"
#include <vector>
#include <memory>
#include <functional>

namespace enc
{
  class WildshapeUtils
  {
  public:
    using CombatantFactory = std::function<std::unique_ptr<Combatant>(const std::string &)>;

    static std::vector<CombatantFactory> getAvailableWildshapeForms(int level, AbilityType actionType);

    static std::vector<std::shared_ptr<Wildshape>> preallocateWildshapeForms(Combatant *combatant, AbilityType actionType, WildshapeFactory &factory);

  private:
    // Prevent instantiation
    WildshapeUtils() = delete;
  };

} // namespace enc
