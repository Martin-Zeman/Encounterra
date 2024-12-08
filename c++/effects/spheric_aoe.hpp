#pragma once

#include <vector>
#include "core/types.hpp"

namespace enc
{

  class SphericAoe
  {
  public:
    SphericAoe(const Coord &coord, int radius) : _origin(coord), _radius(radius) { _affectedCoords = calculateAffectedCoords(); }

    virtual ~SphericAoe() = default;

    const CoordVector &getAffectedCoords() const;

  protected:
    Coord _origin;
    int _radius;
    CoordVector _affectedCoords;

  private:
    CoordVector calculateAffectedCoords() const;
  };
}
