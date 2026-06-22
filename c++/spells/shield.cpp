#include "spells/shield.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include <memory>

namespace enc
{

  std::vector<std::shared_ptr<Actoid>> ShieldFactory::createAll(void *previousActionInDag)
  {
    return {std::make_shared<Shield>(*this)};
  }

  std::shared_ptr<Actoid> ShieldFactory::create(void *target)
  {
    return std::make_shared<Shield>(*this);
  }

  double Shield::calculateThreat(const Kwargs &kwargs)
  {
    return 0.0; // Shield is a defensive reactive buff with no offensive threat
  }

  std::optional<CoordVector>
  Shield::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
  }

} // namespace enc
