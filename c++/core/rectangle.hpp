#pragma once

#include "types.hpp"
#include <array>

namespace enc
{
  class Rectangle
  {
  public:
    virtual std::array<Coord, 4> getCorners() const = 0;
    virtual Vector2D getCenter() const = 0;
  };
}