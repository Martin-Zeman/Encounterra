#pragma once

#include <vector>
#include <array>
#include <cmath>
#include <algorithm>
#include "misc.hpp"
#include "types.hpp"
#include "combatant.hpp"

namespace enc
{

  class Coords
  {
  public:
    Coords(const Coord &coord, Size size = Size::MEDIUM);
    Coords(const Coord &coord, const Combatant& combatant);

    const CoordVector &get() const { return _coords; }
    void set(const CoordVector &newCoords) { _coords = newCoords; }
    size_t rows() const {return std::max(size_t(1), static_cast<size_t>(_size) + 1);}

    std::array<Coord, 4> getCorners() const;

    std::array<double, 2> getCenter() const;

    Coords operator+(const Coord &other) const;
    int operator()(size_t row, size_t col) const;

  private:
    Size _size;
    CoordVector _coords;

    void initCoords(const Coord &coord);
  };
}