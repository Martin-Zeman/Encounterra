#include "coords.hpp"

namespace enc
{
  Coords::Coords(const Coord &coord, Size size) : _size(size) { initCoords(coord); }

  Coords::Coords(const Coord &coord, const Combatant &combatant) : _size(combatant.getSize()) { initCoords(coord); }

  Coords::Coords(const Coords &existingCoords, const Coord &increment) : _size(existingCoords._size), _numCoords(existingCoords._numCoords)
  {
    _coords.reserve(existingCoords._coords.size());
    for(const auto &coord : existingCoords._coords)
      {
        _coords.push_back({coord[0] + increment[0], coord[1] + increment[1]});
      }
  }

  Coords::Coords(const CoordVector &coords) : _size(Size::CUSTOM), _coords(coords), _numCoords(coords.size()) {}

  std::array<Coord, 4> Coords::getCorners() const
  {
    int sizeValue = std::max(0, static_cast<int>(_size));
    return {_coords[0],
            {_coords[0][0] + sizeValue + 1, _coords[0][1]},
            {_coords[0][0], _coords[0][1] + sizeValue + 1},
            {_coords[0][0] + sizeValue + 1, _coords[0][1] + sizeValue + 1}};
  }

  Vector2DBlaze Coords::getCenter() const
  {
    int sizeValue = std::max(0, static_cast<int>(_size));
    return {_coords[0][0] + static_cast<double>(sizeValue + 1) / 2.0, _coords[0][1] + static_cast<double>(sizeValue + 1) / 2.0};
  }

  Coords Coords::operator+(const Coord &other) const { return Coords(*this, other); }

  void Coords::initCoords(const Coord &coord)
  {
    switch(_size)
      {
      case Size::MEDIUM:
      case Size::TINY:
      case Size::SMALL:
        _coords = {coord};
        _numCoords = 1;
        break;
      case Size::LARGE:
        _coords = {coord, {coord[0], coord[1] + 1}, {coord[0] + 1, coord[1]}, {coord[0] + 1, coord[1] + 1}};
        _numCoords = 4;
        break;
      case Size::HUGE:
        _coords.reserve(9);
        for(int i = 0; i < 3; ++i)
          {
            for(int j = 0; j < 3; ++j)
              {
                _coords.push_back({coord[0] + i, coord[1] + j});
              }
          }
        _numCoords = 9;
        break;
      case Size::GARGANTUAN:
        _coords.reserve(16);
        for(int i = 0; i < 4; ++i)
          {
            for(int j = 0; j < 4; ++j)
              {
                _coords.push_back({coord[0] + i, coord[1] + j});
              }
          }
        _numCoords = 16;
        break;
      default: _coords = {coord}; break;
      }
  }

  int Coords::operator()(size_t row, size_t col) const
  {
    if(row >= _coords.size() || col > 1)
      {
        throw std::out_of_range("Index out of range");
      }
    return _coords[row][col];
  }
}
