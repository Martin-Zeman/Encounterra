#include "spells/misty_step.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/geometry.hpp"

namespace enc
{

  MistyStepFactory::MistyStepFactory(Combatant * caster, Resource *resource)
      : ActoidFactory("MistyStepFactory", "Misty Step", caster, AbilityType::MISTY_STEP), _resource(resource)
  {}

  std::optional<Coord> MistyStepFactory::getEligibleTargets() const
  {
    if(_combatant->getSwallowerPtr())
      {
        return std::nullopt;
      }

    return Coord{0, 0};
  }

  std::vector<Actoid *> MistyStepFactory::createAll(void *previousActionInDag)
  {
    auto coord = getEligibleTargets();
    if(coord.has_value())
      {
        return {new MistyStep(*coord, *this)};
      }
    return {};
  }

  Actoid *MistyStepFactory::create(void *target)
  {
    if(!target)
      {
        return nullptr;
      }
    return new MistyStep(*static_cast<Coord *>(target), *this);
  }

  MistyStep::MistyStep(const Coord &coord, const MistyStepFactory &factory)
      : Actoid(const_cast<MistyStepFactory &>(factory), ActoidFlags::IS_SPELL, AbilityType::MISTY_STEP), _coord(coord), _factory(factory)
  {}

  double MistyStep::calculateThreat(const Kwargs &kwargs)
  {
    return 0.0; // Misty Step is handled differently
  }

  MistyStep::~MistyStep() = default;

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

  std::optional<CoordVector>
  MistyStep::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    auto combatant = _factory._combatant;
    if(combatant->getSwallowerPtr())
      {
        return std::nullopt;
      }

    auto &battleMap = BattleMap::getInstance();

    const Coords &combatantPos = battleMap.getCombatantCoordinates(*combatant);
    return CoordVector{combatantPos.getRoot()};
  }

} // namespace enc
