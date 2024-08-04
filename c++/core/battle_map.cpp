#include "battle_map.hpp"
#include "geometry.hpp"
#include <algorithm>
#include <limits>
#include <stdexcept>

namespace enc
{

  std::unique_ptr<BattleMap> BattleMap::_instance = nullptr;

  BattleMap::BattleMap(size_t size = 15)
      : _size(size), _combatantGrid(size, size, -1), // Initialize combatantGrid with -1 (no combatant)
        _terrainGrid(size, size, static_cast<int>(Terrain::NORMAL_TERRAIN))
  // _occupancyGrid(size, size, static_cast<int>(Occupancy::FREE))
  {}

  BattleMap &BattleMap::getInstance(size_t size)
  {
    if(!_instance)
      {
        _instance = std::unique_ptr<BattleMap>(new BattleMap(size));
      }
    return *_instance;
  }

  void BattleMap::resetInstance(size_t size) { _instance.reset(new BattleMap(size)); }

  bool BattleMap::isEmptyOrSelf(int x, int y, int combatant_id) const
  {
    return (_combatantGrid(x, y) == -1 && _terrainGrid(x, y) != static_cast<int>(Terrain::IMPASSABLE_TERRAIN))
           || (_combatantGrid(x, y) != -1 && _combatantGrid(x, y) == combatant_id);
  }

  size_t BattleMap::getGridSize() const { return _size; }

  std::vector<Coord> BattleMap::getFreeCoordsInHopRange(const Coords &target, const blaze::DynamicVector<double> &distances, int mover_size, int rng,
                                                        int combatant_id) const
  {
    assert(rng > 0);
    auto inflated = inflateCoords(target, mover_size);
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


std::vector<Coord> BattleMap::getFreeCoordsInCartesianRange(const Coords& target, const blaze::DynamicVector<double>& distances,
                                                            int mover_size, int rng, int combatant_id) const
{
    assert(rng > 0);
    auto inflated = inflateCoords(target, mover_size);
    std::unordered_set<Coord> coords_in_range;

    for (const auto& coord : inflated)
    {
        for (int i = -rng; i <= rng; ++i)
        {
            for (int j = -rng; j <= rng; ++j)
            {
                int x = coord[0] + i;
                int y = coord[1] + j;

                if (x < 0 || x >= static_cast<int>(_size) || y < 0 || y >= static_cast<int>(_size) ||
                    getCartesianDistanceCoords(target, Coords(Coord{x, y}, Size::MEDIUM)) > rng)
                {
                    continue;
                }

                bool consider_accessibility = distances.size() > 0 ? 
                    distances[x * _size + y] < std::numeric_limits<double>::max() : true;

                if (isEmptyOrSelf(x, y, combatant_id) && consider_accessibility)
                {
                    coords_in_range.insert(Coord{x, y});
                }
            }
        }
    }

    return std::vector<Coord>(coords_in_range.begin(), coords_in_range.end());
}

  void BattleMap::setCombatantCoordinates(const Combatant &combatant, const Coord &coord)
  {
    auto coords = Coords(coord, combatant);
    auto coordPairs = coords.get();
    for(const auto &[x, y] : coordPairs)
      {
        if(x >= _size || y >= _size)
          {
            throw std::out_of_range("Coordinate out of bounds.");
          }

        if(_terrainGrid(x, y) == static_cast<int>(Terrain::IMPASSABLE_TERRAIN))
          {
            throw std::runtime_error("Cannot place combatant at (" + std::to_string(x) + ", " + std::to_string(y) + "): Impassable terrain.");
          }
        // if (_occupancyGrid(x, y) == static_cast<int>(Occupancy::OCCUPIED_BY_COMBATANT) && _combatantGrid(x, y) != combatant._id) {
        if(_combatantGrid(x, y) != -1 && _combatantGrid(x, y) != combatant._id)
          {
            throw std::runtime_error("Cannot place combatant at (" + std::to_string(x) + ", " + std::to_string(y)
                                     + "): Already occupied by another combatant.");
          }

        _combatantGrid(x, y) = combatant._id;
        // _occupancyGrid(x, y) = static_cast<int>(Occupancy::OCCUPIED_BY_COMBATANT);
      }

    // Update the combatant_coordinate_cache using the combatant ID
    // _combatantCoordinateCache.emplace(combatant._id, coords);
    _combatantCoordinateCache.insert_or_assign(combatant._id, coords);
  }

  const Coords &BattleMap::getCombatantCoordinates(const Combatant &combatant) const { return _combatantCoordinateCache.at(combatant._id); }

  bool BattleMap::placeTerrain(const Coord &coord, Terrain terrainType, int radius)
  {
    auto isOverlapping = [this](const Coord &coord, int radius) {
      for(int xOffset = -radius; xOffset <= radius; ++xOffset)
        {
          for(int yOffset = -radius; yOffset <= radius; ++yOffset)
            {
              int x = coord[0] + xOffset;
              int y = coord[1] + yOffset;
              if(x >= 0 && x < _size && y >= 0 && y < _size)
                {
                  if(_terrainGrid(x, y) != static_cast<int>(Terrain::NORMAL_TERRAIN))
                    {
                      return true;
                    }
                }
            }
        }
      return false;
    };

    if(radius == 0)
      {
        int x = std::max(0, std::min(coord[0], static_cast<int>(_size) - 1));
        int y = std::max(0, std::min(coord[1], static_cast<int>(_size) - 1));
        if(isOverlapping({x, y}, radius))
          {
            return false;
          }

        if(terrainType == Terrain::IMPASSABLE_TERRAIN)
          {
            _terrainGrid(x, y) = static_cast<int>(Terrain::IMPASSABLE_TERRAIN);
            _impassableSet.insert({x, y});
            _obstacles.emplace_back(Coord{x, y});
          }
        else if(terrainType == Terrain::DIFFICULT_TERRAIN)
          {
            _terrainGrid(x, y) = static_cast<int>(Terrain::DIFFICULT_TERRAIN);
            _difficultSet.insert({x, y});
          }
      }
    else if(radius > 0)
      {
        if(isOverlapping(coord, radius))
          {
            return false;
          }

        if(terrainType == Terrain::IMPASSABLE_TERRAIN)
          {
            _obstacles.emplace_back(coord, radius);
          }
        for(int xOffset = -radius; xOffset <= radius; ++xOffset)
          {
            for(int yOffset = -radius; yOffset <= radius; ++yOffset)
              {
                int x = std::max(0, std::min(coord[0] + xOffset, static_cast<int>(_size) - 1));
                int y = std::max(0, std::min(coord[1] + yOffset, static_cast<int>(_size) - 1));
                if(x >= 0 && x < _size && y >= 0 && y < _size)
                  {
                    if(terrainType == Terrain::IMPASSABLE_TERRAIN)
                      {
                        _terrainGrid(x, y) = static_cast<int>(Terrain::IMPASSABLE_TERRAIN);
                        _impassableSet.insert({x, y});
                      }
                    else if(terrainType == Terrain::DIFFICULT_TERRAIN)
                      {
                        _terrainGrid(x, y) = static_cast<int>(Terrain::DIFFICULT_TERRAIN);
                        _difficultSet.insert({x, y});
                      }
                  }
              }
          }
      }
    return true;
  }
};
