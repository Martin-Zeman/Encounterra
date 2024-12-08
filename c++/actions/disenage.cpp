#include "actions/disengage.hpp"

namespace enc
{

  std::vector<std::shared_ptr<Actoid>> DisengageFactory::createAll(void *previousActionInDag) { return {std::make_shared<Disengage>(*this)}; }

  std::shared_ptr<Actoid> DisengageFactory::create(void *target) { return std::make_shared<Disengage>(*this); }

  std::optional<CoordVector>
  Disengage::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    return {};
  }
}
