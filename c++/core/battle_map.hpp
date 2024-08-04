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
    static void resetInstance(size_t size = 15);

    size_t getGridSize() const;

    std::vector<Coord> getFreeCoordsInHopRange(const Coords &target, const blaze::DynamicVector<double> &distances = blaze::DynamicVector<double>(),
                                               int mover_size = static_cast<int>(Size::MEDIUM), int rng = 1, int combatant_id = -1) const;

    void setCombatantCoordinates(const Combatant &combatant, const Coord &coord);
    const Coords& getCombatantCoordinates(const Combatant& combatant) const;

  private:
    size_t _size;
    blaze::DynamicMatrix<int> _combatantGrid;
    blaze::DynamicMatrix<int> _terrainGrid;
    // blaze::DynamicMatrix<int> _occupancyGrid TODO: This may actually not be needed
    std::unordered_map<int, Coords> _combatantCoordinateCache;
    static std::unique_ptr<BattleMap> _instance;

    BattleMap(size_t size);
    BattleMap(const BattleMap &) = delete;
    BattleMap &operator=(const BattleMap &) = delete;

    bool isEmptyOrSelf(int x, int y, int combatant_id) const;
  };
}
