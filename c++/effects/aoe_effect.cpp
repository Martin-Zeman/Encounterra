#include "effects/aoe_effect.hpp"
#include "core/battle_map.hpp"
#include "core/types.hpp"
#include "core/combatant.hpp"
#include "core/geometry.hpp"

namespace enc
{
  bool AoeEffect::isAffecting(Combatant *combatant) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    std::vector<Coord> coords = getAffectedCoords();

    return getHopDistanceCoords(battleMap.getCombatantCoordinates(*combatant), coords) == 0;
  }
}
