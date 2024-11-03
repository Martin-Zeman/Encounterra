#include "effects/spheric_aoe.hpp"

namespace enc
{
  std::vector<Coord> SphericAoe::calculateAffectedCoords() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    int gridSize = battleMap.getSize();
    std::vector<Coord> coords;

    blaze::StaticVector<double, 2> originCenter = getSquareCenter(_origin);

    for(int i = -_radius; i <= _radius; ++i)
      {
        for(int j = -_radius; j <= _radius; ++j)
          {
            int x = _origin[0] + i;
            int y = _origin[1] + j;

            if(x < 0 || x >= gridSize || y < 0 || y >= gridSize)
              {
                continue;
              }

            Coord currentCoord({x, y});
            blaze::StaticVector<double, 2> currentCenter = getSquareCenter(currentCoord);

            // Calculate Euclidean distance
            double distance = std::sqrt(std::pow(originCenter[0] - currentCenter[0], 2) + std::pow(originCenter[1] - currentCenter[1], 2));

            if(distance <= _radius)
              {
                coords.push_back(currentCoord);
              }
          }
      }

    return coords;
  }

  const std::vector<Coord> &SphericAoe::getAffectedCoords() const { return _affectedCoords; }
}
