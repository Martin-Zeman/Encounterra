#include "spells/misty_step.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include <memory>

namespace enc
{

  std::vector<std::shared_ptr<Actoid>> MistyStepFactory::createAll(void *previousActionInDag)
  {
    Combatant *swallower = _combatant->getSwallower();
    if(swallower)
      {
        return {}; // Can't see while being swallowed
      }
    Coord target{0, 0};
    return {std::make_shared<MistyStep>(target, *this)};
  }

  std::shared_ptr<Actoid> MistyStepFactory::create(void *target)
  {
    Coord *coord = static_cast<Coord *>(target);
    return std::make_shared<MistyStep>(*coord, *this);
  }

  double MistyStep::calculateThreat(const Kwargs &kwargs)
  {
    return 0.0; // Misty Step is handled differently
  }

  std::optional<CoordVector>
  MistyStep::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    if(_factory._combatant->getSwallower())
      {
        return std::nullopt;
      }
    BattleMap &battleMap = BattleMap::getInstance();
    return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
  }

} // namespace enc