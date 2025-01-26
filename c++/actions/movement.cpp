#include "actions/movement.hpp"
#include "core/combatant.hpp"

namespace enc
{
  const std::unordered_map<AbilityType, std::string> MovementFactory::MOVEMENT_TYPE_NAMES
    = {{AbilityType::STANDARD_MOVEMENT, "Standard Movement"},
       {AbilityType::DISENGAGED_MOVEMENT, "Disengaged Movement"},
       {AbilityType::FORCED_MOVEMENT, "Forced Movement"},
       {AbilityType::GET_UP_FROM_PRONE, "Get Up From Prone"}};

  MovementFactory::MovementFactory(Combatant& combatant, CoordVector path, AbilityType movementType)
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

        increments.push_back(std::make_shared<MovementIncrement>(increment, isStandardMovement, static_cast<ActoidFactory &>(*this)));

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

  size_t MovementIncrement::hash() const
  {
    size_t h = std::hash<uint32_t>{}(_actoidFlags);
    h ^= std::hash<int>{}(_increment[0]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_increment[1]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<bool>{}(_incursAOO) + 0x9e3779b9 + (h << 6) + (h >> 2);
    return h;
  }

  bool MovementIncrement::equals(const Actoid &other) const
  {
    if(auto *o = dynamic_cast<const MovementIncrement *>(&other))
      {
        return _increment == o->_increment && _incursAOO == o->_incursAOO && _actoidFlags == o->_actoidFlags;
      }
    return false;
  }

  std::optional<CoordVector>
  MovementIncrement::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &coords)
  {
    // Movement increment doesn't need to calculate eligible coords
    return std::nullopt;
  }

  std::string MovementIncrement::toString() const { return "(" + std::to_string(_increment[0]) + ", " + std::to_string(_increment[1]) + ")"; }

  size_t GetUpFromProne::hash() const { return std::hash<int>{}(static_cast<int>(getFlags())); }

  bool GetUpFromProne::equals(const Actoid &other) const
  {
    if(auto *getUp = dynamic_cast<const GetUpFromProne *>(&other))
      {
        return getFlags() == other.getFlags();
      }
    return false;
  }

  std::optional<CoordVector> GetUpFromProne::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &coords)
  {
    // Getting up happens in place, no eligible coords needed
    return std::nullopt;
  }

  std::string GetUpFromProne::toString() const { return "Get Up From Prone"; }
}