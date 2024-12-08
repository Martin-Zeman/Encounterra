#pragma once

#include <vector>
#include "core/types.hpp"

namespace enc
{
  class SquareAoe
  {
  public:
    SquareAoe(const Coord &origin, int length);

    virtual ~SquareAoe() = default;

    const CoordVector &getAffectedCoords() const;

  protected:
    Coord _origin;
    int _length;
    CoordVector _affectedCoords;
  };
}
