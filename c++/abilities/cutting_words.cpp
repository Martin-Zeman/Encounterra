#include "abilities/cutting_words.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include <memory>

namespace enc
{
  std::vector<std::shared_ptr<Actoid>> CuttingWordsFactory::createAll(void *previousActionInDag) { return {std::make_shared<CuttingWords>(*this)}; }

  std::shared_ptr<Actoid> CuttingWordsFactory::create(void *target) { return std::make_shared<CuttingWords>(*this); }

  double CuttingWords::calculateThreat(const Kwargs &kwargs)
  {
    return 0.0; // Cutting Words is a defensive reaction with no offensive threat of its own.
  }

  std::optional<CoordVector> CuttingWords::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    return CoordVector{BattleMap::getInstance().getCombatantCoordinates(*_factory._combatant).getRoot()};
  }
}
