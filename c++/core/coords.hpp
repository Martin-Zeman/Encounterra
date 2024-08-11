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
    Coords(const Coords &existingCoords, const Coord &increment);

    const CoordVector &get() const { return _coords; }
    void set(const CoordVector &newCoords) { _coords = newCoords; }
    size_t numCoords() const {return _numCoords;}

    std::array<Coord, 4> getCorners() const;

    std::array<double, 2> getCenter() const;

    Coords operator+(const Coord &other) const;
    int operator()(size_t row, size_t col) const;

  private:
    Size _size;
    CoordVector _coords;
    size_t _numCoords;

    void initCoords(const Coord &coord);
  };
}