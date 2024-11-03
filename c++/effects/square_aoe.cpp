#include "effects/square_aoe.hpp"

namespace enc
{
  SquareAoe::SquareAoe(const Coord &origin, int length) : _origin(origin), _length(length)
  {
    _affectedCoords = BattleMap::getInstance().getCoordsAffectedBySquareAoe(_origin, _length);
  }

  const std::vector<Coord> &SquareAoe::getAffectedCoords() const { return _affectedCoords; }
}
