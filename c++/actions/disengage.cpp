#include "actions/disengage.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"

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
    // Both the base-action Disengage and Cunning Action's bonus Disengage are location independent: they are
    // always available from the current square, provided the combatant can actually move. Mirrors the Python
    // Disengage.get_eligible_coords (returns None when Grappled/Grappling/Restrained/Swallowed or movement 0).
    Combatant *combatant = _factory.getCombatant();
    if(combatant->getSwallower() != nullptr || combatant->getMovement() == 0
       || combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return std::nullopt;
      }
    return CoordVector{BattleMap::getInstance().getCombatantCoordinates(*combatant).getRoot()};
  }

  std::string Disengage::toString() const
  {
    std::string prefix = _factory.getAbilityType() == AbilityType::CUNNING_DISENGAGE ? "Cunning " : "";
    return prefix + "Disengage of " + _factory.getCombatant()->_name;
  }
}
