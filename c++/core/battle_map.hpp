#pragma once

#include <blaze/Math.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include <limits>
#include <random>
#include <stdexcept>
#include "misc.hpp"
#include "types.hpp"
#include "coords.hpp"
#include "combatant.hpp"

namespace enc
{

  class BattleMap
  {
  public:
    static BattleMap &getInstance(size_t size = 15);

    // void initializeGrid(size_t size = 15U);

    // void setGridValue(size_t x, size_t y, int value);

    // int getGridValue(size_t x, size_t y) const;

    size_t getGridSize() const;

    std::vector<Coord> getFreeCoordsInHopRange(const Coords &coords, const blaze::DynamicVector<double> &distances = blaze::DynamicVector<double>(),
                                               int inflate_to_dist = static_cast<int>(Size::MEDIUM), int rng = 1, int combatant_id = -1) const;

    void setCombatantCoordinates(const Combatant &combatant, const Coords &coords);

  private:
    size_t _size;
    blaze::DynamicMatrix<int> _combatantGrid;
    blaze::DynamicMatrix<int> _terrainGrid;
    blaze::DynamicMatrix<int> _occupancyGrid;
    std::unordered_map<int, Coords> _combatantCoordinateCache;

    BattleMap(size_t size);
    BattleMap(const BattleMap &) = delete;
    BattleMap &operator=(const BattleMap &) = delete;

    bool isEmptyOrSelf(int x, int y, int combatant_id) const;
  };
}
