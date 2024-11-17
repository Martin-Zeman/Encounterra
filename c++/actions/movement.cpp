#include "actions/movement.hpp"
#include "core/combatant.hpp"

namespace enc
{
  const std::unordered_map<AbilityType, std::string> MovementFactory::MOVEMENT_TYPE_NAMES
    = {{AbilityType::STANDARD_MOVEMENT, "Standard Movement"},
       {AbilityType::DISENGAGED_MOVEMENT, "Disengaged Movement"},
       {AbilityType::FORCED_MOVEMENT, "Forced Movement"},
       {AbilityType::GET_UP_FROM_PRONE, "Get Up From Prone"}};

  MovementFactory::MovementFactory(Combatant *combatant, std::vector<Coord> path, AbilityType movementType)
      : ActoidFactory("MovementFactory", MOVEMENT_TYPE_NAMES.at(movementType), combatant, movementType), _path(path)
  {}

  std::vector<std::shared_ptr<Actoid>> MovementFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> increments;
    increments.reserve(_path.size());

    bool isStandardMovement = (getAbilityType() == AbilityType::STANDARD_MOVEMENT);

    for(const auto &increment : _path)
      {
        // if(!_combatant->hasMovement()) actually, how much movement a combatant has should not enter into this
        //   break;

        increments.push_back(std::make_shared<MovementIncrement>(increment, isStandardMovement, *this));

        // _combatant->decrementMovement();
      }

    return increments;
  }

  std::shared_ptr<Actoid> MovementFactory::create(void *target)
  {
    if(_path.empty())
      return nullptr;

    auto increment = _path.front();
    _path.erase(_path.begin());

    return std::make_shared<MovementIncrement>(increment, getAbilityType() == AbilityType::STANDARD_MOVEMENT, *this);
  }

  std::shared_ptr<Actoid> GetUpFactory::create(void *target) { return std::make_shared<GetUpFromProne>(*this); }
}