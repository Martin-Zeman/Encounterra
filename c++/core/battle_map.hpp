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

namespace enc
{

  class BattleMap
  {
  private:
    blaze::DynamicMatrix<int> grid;

    BattleMap() = default;
    BattleMap(const BattleMap &) = delete;
    BattleMap &operator=(const BattleMap &) = delete;

    bool isEmptyOrSelf(int x, int y, int combatant_id) const;

  public:
    static BattleMap &getInstance();

    void initializeGrid(size_t size = 15U);

    void setGridValue(size_t x, size_t y, int value);

    int getGridValue(size_t x, size_t y) const;

    size_t getGridSize() const;

    std::vector<Coord> getFreeCoordsInHopRange(const blaze::DynamicMatrix<double> &coords,
                                               const blaze::DynamicVector<double> &distances = blaze::DynamicVector<double>(),
                                               int inflate_to_dist = static_cast<int>(Size::MEDIUM), int rng = 1, int combatant_id = -1) const;
  };
}
