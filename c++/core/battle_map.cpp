#include "battle_map.hpp"
#include "geometry.hpp"
#include <algorithm>
#include <limits>
#include <stdexcept>

namespace enc
{

  BattleMap &BattleMap::getInstance()
  {
    static BattleMap instance;
    return instance;
  }

  bool BattleMap::isEmptyOrSelf(int x, int y, int combatant_id) const
  {
    // Implement this function based on your grid representation
    // This is a placeholder implementation
    return _grid(x, y) == 0 || _grid(x, y) == combatant_id;
  }

  void BattleMap::initializeGrid(size_t size)
  {
    _grid.resize(size, size);
    _grid = 0; // Initialize all elements to 0
  }

  void BattleMap::setGridValue(size_t x, size_t y, int value)
  {
    if(x >= _grid.rows() || y >= _grid.columns())
      {
        throw std::out_of_range("Coordinates out of range");
      }
    _grid(x, y) = value;
  }

  int BattleMap::getGridValue(size_t x, size_t y) const
  {
    if(x >= _grid.rows() || y >= _grid.columns())
      {
        throw std::out_of_range("Coordinates out of range");
      }
    return _grid(x, y);
  }

  size_t BattleMap::getGridSize() const
  {
    return _grid.rows(); // Assuming square grid
  }

  std::vector<Coord>
  BattleMap::getFreeCoordsInHopRange(const blaze::DynamicMatrix<double> &coords,
                                     const blaze::DynamicVector<double> &distances,
                                     int inflate_to_dist, int rng, int combatant_id) const
  {
    assert(rng > 0);
    size_t size = _grid.rows();
    auto inflated = inflateCoords(coords, inflate_to_dist);
    std::vector<Coord> adjacent_coords;

    for(const auto &coord : inflated)
      {
        for(int i = -rng; i <= rng; ++i)
          {
            for(int j = -rng; j <= rng; ++j)
              {
                int x = coord[0] + i;
                int y = coord[1] + j;

                if(x < 0 || x >= static_cast<int>(size) || y < 0 || y >= static_cast<int>(size))
                  {
                    continue;
                  }

                bool consider_accessibility = distances.size() > 0 ? distances[x * size + y] < std::numeric_limits<double>::max() : true;

                if(isEmptyOrSelf(x, y, combatant_id) && consider_accessibility)
                  {
                    adjacent_coords.emplace_back(x, y);
                  }
              }
          }
      }

    // Remove duplicates
    std::sort(adjacent_coords.begin(), adjacent_coords.end());
    adjacent_coords.erase(std::unique(adjacent_coords.begin(), adjacent_coords.end()), adjacent_coords.end());

    return adjacent_coords;
  }
};
