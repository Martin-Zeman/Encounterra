#pragma once

#include <blaze/Math.h>
#include <array>
#include <utility>
#include <any>
#include <map>
#include <unordered_map>
#include <ostream>

namespace enc
{

  using Coord = std::array<int, 2>;
  using CoordVector = std::vector<Coord>;
  using Die = blaze::StaticVector<uint8_t, 2>;
  using MapMatrix = blaze::DynamicMatrix<int>;
  using Vector2D = blaze::StaticVector<double, 2UL>;
  // using Vector2D = std::array<double, 2>;

  enum class Color
  {
    BLUE = 1,
    RED = 2
  };

  inline const std::unordered_map<Color, std::string_view> COLOR_NAMES{
    {Color::BLUE, "BLUE"},
    {Color::RED, "RED"}
  };

  enum class AbilityActionType
  {
    ACTION,
    BONUS_ACTION,
    REACTION,
    HASTE_ACTION,
    PASSIVE
  };

  using Kwargs = std::map<std::string, std::any>;
}

namespace std
{
  template <> struct hash<enc::Coord>
  {
    std::size_t operator()(const enc::Coord &coord) const { return std::hash<int>()(coord[0]) ^ (std::hash<int>()(coord[1]) << 1); }
  };

  template <> struct hash<enc::Die>
  {
    size_t operator()(const enc::Die &d) const { return std::hash<uint8_t>()(d[0]) ^ (std::hash<uint8_t>()(d[1]) << 1); }
  };

  template <> struct hash<std::pair<enc::Die, int>>
  {
    size_t operator()(const std::pair<enc::Die, int> &p) const { return std::hash<enc::Die>()(p.first) ^ std::hash<int>()(p.second); }
  };
}

inline std::ostream& operator<<(std::ostream& os, const enc::Coord& coord) {
    os << "(" << coord[0] << ", " << coord[1] << ")";
    return os;
}

inline std::ostream &operator<<(std::ostream &os, const enc::Die &die) { return os << std::to_string(die[0]) + "d" + std::to_string(die[1]); }
