#pragma once

#include <vector>

namespace enc
{
  class SquareAoe
  {
  public:
    SquareAoe(const Coord &origin, int length);

    virtual ~SquareAoe() = default;

    const std::vector<Coord> &getAffectedCoords() const;

  protected:
    Coord _origin;
    int _length;
    std::vector<Coord> _affectedCoords;
  };
}
