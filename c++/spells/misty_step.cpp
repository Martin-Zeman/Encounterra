#include "spells/misty_step.hpp"

namespace enc
{

  MistyStepFactory::MistyStepFactory(Combatant *caster, Resource *resource)
      : ActoidFactory("MistyStepFactory", "Misty Step", caster, AbilityType::MISTY_STEP), _resource(resource)
  {}

  MistyStep::MistyStep(const Coord &coord, const MistyStepFactory &factory)
      : Actoid(const_cast<MistyStepFactory &>(factory), ActoidFlags::IS_SPELL, AbilityType::MISTY_STEP), _coord(coord), _factory(factory)
  {}

  size_t MistyStep::hash() const
  {
    size_t h = std::hash<int>{}(static_cast<int>(getAbilityType()));
    h ^= std::hash<int>{}(static_cast<int>(getFlags())) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_coord[0]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_coord[1]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    return h;
  }

  bool MistyStep::equals(const Actoid &other) const
  {
    if(auto *mistyStep = dynamic_cast<const MistyStep *>(&other))
      {
        return getAbilityType() == other.getAbilityType() && getFlags() == other.getFlags() && _coord == mistyStep->_coord;
      }
    return false;
  }

} // namespace enc
