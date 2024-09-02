#pragma once

#include <blaze/Math.h>
#include <array>

namespace enc
{

  using Coord = std::array<int, 2>;
  using CoordVector = std::vector<Coord>;
  using Die = blaze::StaticVector<uint8_t, 2>;
  using MapMatrix = blaze::DynamicMatrix<int>;
  using Vector2DBlaze = blaze::StaticVector<double, 2UL>;
  using Vector2D = std::array<double, 2>;

  enum class Color
  {
    BLUE = 1,
    RED = 2
  };

}

namespace std
{
  template <> struct hash<enc::Coord>
  {
    std::size_t operator()(const enc::Coord &coord) const { return std::hash<int>()(coord[0]) ^ (std::hash<int>()(coord[1]) << 1); }
  };
}
