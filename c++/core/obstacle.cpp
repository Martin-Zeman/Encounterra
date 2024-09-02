#include "obstacle.hpp"

namespace enc
{

  // std::vector<std::array<int64_t, 2>> Obstacle::getCorners() const
  // {
  //   return {{_coord[0] - _radius, _coord[1] - _radius},
  //           {_coord[0] + _radius + 1, _coord[1] - _radius},
  //           {_coord[0] - _radius, _coord[1] + _radius + 1},
  //           {_coord[0] + _radius + 1, _coord[1] + _radius + 1}};
  // }

    std::array<Coord, 4> Obstacle::getCorners() const
    {
        return {{
            {_coord[0] - _radius, _coord[1] - _radius},
            {_coord[0] + _radius + 1, _coord[1] - _radius},
            {_coord[0] - _radius, _coord[1] + _radius + 1},
            {_coord[0] + _radius + 1, _coord[1] + _radius + 1}
        }};
    }

  Vector2D Obstacle::getCenter() const { return {static_cast<double>(_coord[0]) + 0.5, static_cast<double>(_coord[1]) + 0.5}; }
}
