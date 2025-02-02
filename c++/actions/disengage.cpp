#include "actions/disengage.hpp"

namespace enc
{

  // std::vector<Actoid *> DisengageFactory::createAll(void *previousActionInDag)
  // {
  //   std::vector<Actoid *> ret;
  //   ret.push_back(std::make_shared<Disengage>(static_cast<ActoidFactory &>(*this)));
  //   return ret;
  // }

  std::vector<Actoid *> DisengageFactory::createAll(void *previousActionInDag)
  {
    Disengage d(static_cast<ActoidFactory &>(*this));
    return {new Disengage(d)};
  }

  Actoid *DisengageFactory::create(void *target) { return new Disengage(static_cast<ActoidFactory &>(*this)); }

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
