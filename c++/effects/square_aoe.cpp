#include "effects/square_aoe.hpp"
#include "core/geometry.hpp"
#include "core/battle_map.hpp"

namespace enc
{
  SquareAoe::SquareAoe(const Coord &origin, int length) : _origin(origin), _length(length)
  {
    _affectedCoords = getCoordsAffectedBySquareAoE(_origin, _length, BattleMap::getInstance().getGridSize());
  }

  const CoordVector &SquareAoe::getAffectedCoords() const { return _affectedCoords; }
}
