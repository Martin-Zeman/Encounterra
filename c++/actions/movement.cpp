#include "actions/movement.hpp"

namespace enc
{
  std::vector<std::shared_ptr<Actoid>> MovementFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> increments;
    increments.reserve(_path.size());

    bool isStandardMovement = (getAbilityType() == AbilityType::STANDARD_MOVEMENT);

    for(const auto &increment : _path)
      {
        if(!getCombatant()->hasMovement())
          break;

        increments.push_back(std::make_shared<MovementIncrement>(increment, isStandardMovement, *this));

        getCombatant()->decrementMovement(1); // Assuming 1 movement per increment
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