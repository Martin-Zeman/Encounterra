#include "actions/dodge.hpp"

namespace enc
{

  std::vector<std::shared_ptr<Actoid>> DodgeFactory::createAll(void *previousActionInDag) { return {std::make_shared<Dodge>(*this)}; }

  std::shared_ptr<Actoid> DodgeFactory::create(void *target) { return std::make_shared<Dodge>(*this); }

  std::optional<std::vector<Coord>>
  Dodge::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    return {};
  }
}
