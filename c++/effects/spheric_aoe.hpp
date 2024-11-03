#pragma once

#include <vector>

namespace enc
{

  class SphericAoe
  {
  public:
    SphericAoe(const Coord &coord, int radius) : _origin(coord), _radius(radius) { _affectedCoords = getAffectedCoords(); }

    virtual ~SphericAoe() = default;

    const std::vector<Coord> &getAffectedCoords() const;

  protected:
    Coord _origin;
    int _radius;
    std::vector<Coord> _affectedCoords;

  private:
    std::vector<Coord> calculateAffectedCoords() const;
  };
}
