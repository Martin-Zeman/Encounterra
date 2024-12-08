#pragma once

#include <vector>
#include <array>
#include <cmath>
#include <algorithm>
#include "core/misc.hpp"
#include "core/types.hpp"
#include "core/combatant.hpp"
#include "core/rectangle.hpp"

namespace enc
{

  class Coords : public Rectangle
  {
  public:
    Coords(const Coord &coord, Size size = Size::MEDIUM);
    Coords(const Coord &coord, const Combatant& combatant);
    Coords(const Coords &existingCoords, const Coord &increment);
    Coords(const CoordVector &coords);

    const CoordVector &get() const { return _coords; }
    const Coord &getRoot() const { return _coords[0]; }
    void set(const CoordVector &newCoords) { _coords = newCoords; }
    size_t numCoords() const {return _numCoords;}

    std::array<Coord, 4> getCorners() const override;

    Vector2D getCenter() const override;

    Coords operator+(const Coord &other) const;
    int operator()(size_t row, size_t col) const;
    bool areValidCoords(size_t mapSize) const;
    Size getSize() const;

  private:
    Size _size;
    CoordVector _coords;
    size_t _numCoords;

    void initCoords(const Coord &coord);
  };
}