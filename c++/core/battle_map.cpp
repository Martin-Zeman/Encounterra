#include "battle_map.hpp"
#include "geometry.hpp"
#include <algorithm>
#include <limits>
#include <stdexcept>

namespace enc
{

  BattleMap::BattleMap(size_t size = 15) 
        : _size(size), 
          _combatantGrid(size, size, -1), // Initialize combatantGrid with -1 (no combatant)
          _terrainGrid(size, size, static_cast<int>(Terrain::NORMAL_TERRAIN)),
          _occupancyGrid(size, size, static_cast<int>(Occupancy::FREE)) 
    {
    }

  BattleMap &BattleMap::getInstance(size_t size)
  {
    static BattleMap instance(size);
    return instance;
  }

  bool BattleMap::isEmptyOrSelf(int x, int y, int combatant_id) const
  {
    // Implement this function based on your grid representation
    // This is a placeholder implementation
    return _combatantGrid(x, y) == 0 || _combatantGrid(x, y) == combatant_id;
  }

  // void BattleMap::initializeGrid(size_t size)
  // {
  //   _grid.resize(size, size);
  //   _grid = 0; // Initialize all elements to 0
  // }

  // void BattleMap::setGridValue(size_t x, size_t y, int value)
  // {
  //   if(x >= _grid.rows() || y >= _grid.columns())
  //     {
  //       throw std::out_of_range("Coordinates out of range");
  //     }
  //   _grid(x, y) = value;
  // }

  // int BattleMap::getGridValue(size_t x, size_t y) const
  // {
  //   if(x >= _grid.rows() || y >= _grid.columns())
  //     {
  //       throw std::out_of_range("Coordinates out of range");
  //     }
  //   return _grid(x, y);
  // }

  size_t BattleMap::getGridSize() const
  {
    return _size; // Assuming square grid
  }

  std::vector<Coord>
  BattleMap::getFreeCoordsInHopRange(const Coords &coords,
                                     const blaze::DynamicVector<double> &distances,
                                     int inflate_to_dist, int rng, int combatant_id) const
  {
    assert(rng > 0);
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

                if(x < 0 || x >= static_cast<int>(_size) || y < 0 || y >= static_cast<int>(_size))
                  {
                    continue;
                  }

                bool consider_accessibility = distances.size() > 0 ? distances[x * _size + y] < std::numeric_limits<double>::max() : true;

                if(isEmptyOrSelf(x, y, combatant_id) && consider_accessibility)
                  {
                    adjacent_coords.emplace_back(Coord{x, y});
                  }
              }
          }
      }

    // Remove duplicates
    std::sort(adjacent_coords.begin(), adjacent_coords.end());
    adjacent_coords.erase(std::unique(adjacent_coords.begin(), adjacent_coords.end()), adjacent_coords.end());

    return adjacent_coords;
  }

  void BattleMap::setCombatantCoordinates(const Combatant& combatant, const Coords& coords) {
        auto coordPairs = coords.get();
        for (const auto& [x, y] : coordPairs) {
            if (x >= _size || y >= _size) {
                throw std::out_of_range("Coordinate out of bounds.");
            }

            if (_terrainGrid(x, y) == static_cast<int>(Terrain::IMPASSABLE_TERRAIN)) {
                throw std::runtime_error("Cannot place combatant at (" + std::to_string(x) + ", " + std::to_string(y) + "): Impassable terrain.");
            }
            if (_occupancyGrid(x, y) == static_cast<int>(Occupancy::OCCUPIED_BY_COMBATANT) && _combatantGrid(x, y) != combatant._id) {
                throw std::runtime_error("Cannot place combatant at (" + std::to_string(x) + ", " + std::to_string(y) + "): Already occupied by another combatant.");
            }

            _combatantGrid(x, y) = combatant._id;
            _occupancyGrid(x, y) = static_cast<int>(Occupancy::OCCUPIED_BY_COMBATANT);
        }

        // Update the combatant_coordinate_cache using the combatant ID
        _combatantCoordinateCache.emplace(combatant._id, coords);
    }
};
