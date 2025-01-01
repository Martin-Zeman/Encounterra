#include "actions/disengage.hpp"

namespace enc
{

  // std::vector<std::shared_ptr<Actoid>> DisengageFactory::createAll(void *previousActionInDag)
  // {
  //   std::vector<std::shared_ptr<Actoid>> ret;
  //   ret.push_back(std::make_shared<Disengage>(static_cast<ActoidFactory &>(*this)));
  //   return ret;
  // }

  std::vector<std::shared_ptr<Actoid>> DisengageFactory::createAll(void *previousActionInDag)
  {
    Disengage d(static_cast<ActoidFactory &>(*this));
    return {std::shared_ptr<Actoid>(new Disengage(d))};
  }

  std::shared_ptr<Actoid> DisengageFactory::create(void *target) { return std::make_shared<Disengage>(static_cast<ActoidFactory &>(*this)); }

  std::optional<CoordVector>
  Disengage::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    return {};
  }

  std::string Disengage::toString() const { return "Disengage"; }

  size_t Disengage::hash() const {
    return std::hash<int>{}(static_cast<int>(getAbilityType()));
  }

  bool Disengage::equals(const Actoid &other) const {
    return getAbilityType() == other.getAbilityType();
  }
}
