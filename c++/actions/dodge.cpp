#include "actions/dodge.hpp"

namespace enc
{

  // std::vector<std::shared_ptr<Actoid>> DodgeFactory::createAll(void *previousActionInDag) { return {std::make_shared<Dodge>(static_cast<ActoidFactory&>(*this))}; }

  std::vector<std::shared_ptr<Actoid>> DodgeFactory::createAll(void *previousActionInDag)
  {
    Dodge d(static_cast<ActoidFactory &>(*this));
    return {std::shared_ptr<Actoid>(new Dodge(d))};
  }

  std::shared_ptr<Actoid> DodgeFactory::create(void *target) { return std::make_shared<Dodge>(static_cast<ActoidFactory&>(*this)); }

  std::optional<CoordVector>
  Dodge::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    return {};
  }

  std::string Dodge::toString() const { return "Dodge"; }

  size_t Dodge::hash() const {
    return std::hash<int>{}(static_cast<int>(getAbilityType()));
  }

  bool Dodge::equals(const Actoid &other) const {
    return getAbilityType() == other.getAbilityType();
  }
}
