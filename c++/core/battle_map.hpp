#pragma once

#include <blaze/Math.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include <limits>
#include <random>
#include <stdexcept>
#include <optional>
#include <cstdint>
#include "core/misc.hpp"
#include "core/types.hpp"
#include "core/coords.hpp"
#include "core/combatant.hpp"
#include "core/obstacle.hpp"
#include "spells/spell_stats.hpp"

namespace enc
{
  struct PairHash
  {
    template <class T1, class T2> std::size_t operator()(const std::pair<T1, T2> &pair) const
    {
      auto h1 = std::hash<T1>{}(pair.first);
      auto h2 = std::hash<T2>{}(pair.second);
      return h1 ^ (h2 << 1);
    }
  };

  struct DijkstraResult
  {
    blaze::DynamicVector<int> dist;
    blaze::DynamicMatrix<Coord> shortestPaths;
  };

  class BattleMap
  {
  public:
    static BattleMap &getInstance(size_t size = 15);
    static void resetInstance(size_t size = 15);
    std::string toString(bool color = false) const;

    size_t getGridSize() const;

    // Returns every coordinate reachable by the combatant given the Dijkstra shortest-paths matrix (entries of
    // {-1,-1} are unreachable), always including the combatant's current position. Mirrors Python
    // Map.get_all_accessible_coords, used by location-independent actions (e.g. Dash) to fan out over the board.
    CoordVector getAllAccessibleCoords(const blaze::DynamicMatrix<Coord> &shortestPaths, const Combatant &combatant) const;

    CoordVector getFreeCoordsInHopRange(const Coords &target, const blaze::DynamicVector<double> &distances = blaze::DynamicVector<double>(),
                                               Size moverSize = Size::MEDIUM, int rng = 1, int combatantId = -1) const;

    CoordVector getFreeCoordsInCartesianRange(const Coords &target, const blaze::DynamicVector<double> &distances,
                                                     Size moverSize = Size::MEDIUM, int rng = 1, int combatantId = -1) const;

    void setCombatantCoordinates(const Combatant &combatant, const Coord &coord);
    void moveCombatantByIncrement(const Combatant &combatant, const Coord &increment);
    void moveCombatant(const Combatant &combatant, const Coord &newCoord, bool log = false);
    const Coords &getCombatantCoordinates(const Combatant &combatant) const;
    bool placeTerrain(const Coord &coord, Terrain terrainType, int radius = 0);
    MapMatrix buildCombatantAdjacencyMask(const Combatant &combatant, bool consider_aoo = false);
    void buildBaseAdjacencyMatrix();
    DijkstraResult dijkstra(const Coord &src, const MapMatrix &adjMatrix, const MapMatrix &mask);
    DijkstraResult calcDijkstra(const Combatant &combatant);
    CoordVector reconstructFromShortestPath(const blaze::DynamicMatrix<Coord> &shortest_paths, const Coord &source, const Coord &target);
    // Port of numba is_path_straight: true iff the last `length` coords of `path` advance in a single, constant
    // step direction (and the path is at least `length` coords long, with length >= 2). Used by Pounce.
    static bool isPathStraight(const CoordVector &path, int length);
    int getHopDistanceCombatants(const Combatant &combatant1, const Combatant &combatant2) const;
    double getCartesianDistanceCombatants(const Combatant &combatant1, const Combatant &combatant2) const;
    std::unordered_set<Coord> getAdjacentCoords(const Coords &coords) const;
    std::optional<Coord> getNearestFreeAdjacentCoords(const Combatant &combatant, const Coords &myLocation, Size combatantSize,
                                                      const Coords &targetLocation, const blaze::DynamicVector<int> &distances, int rng = 1);
    template <typename DistType>
    std::tuple<const Combatant *, DistType>
    getNearest(const Combatant &combatant, Side side = Side::ENEMY, DistanceMetric distType = DistanceMetric::HOP) const;
    bool isEnemyAdjacent(const Combatant &combatant) const;
    bool isAllyAdjacentToTarget(const Combatant &combatant, const Combatant &target) const;
    std::optional<CoordVector>
    getPathToCombatant(const Combatant &combatant, const Combatant &target, const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                       const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>(), int rng = 1, bool considerAOO = false);
    std::optional<CoordVector>
    getPathToCoord(const Combatant &combatant, const Coord &targetCoord, const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                   const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>(), bool considerAOO = false);
    void removeCombatant(const Combatant &combatant);
    bool removeCombatantIfDead(Combatant &combatant);
    void resetCombatantsToInitialPositions(const std::unordered_map<int, Coords> initialPositions);
    int getCombatantGridValueAt(const Coord &coord) const;
    std::tuple<Coord, int, std::vector<Combatant *>>
    findBestPlacementHarmfulCircular(const Combatant *caster, int spellRange, int radius);
    std::tuple<Coord, int, std::vector<Combatant *>> findBestPlacementHarmfulSquare(const Combatant *caster, int spellRange, int length);
    std::optional<std::tuple<Coord, double, int>> findBestPlacementHarmfulCone(const Combatant *caster, int radius);
    std::optional<std::tuple<Coord, double, int>> findBestPlacementHarmfulLine(const Combatant* caster, int length, int width);

    std::vector<Combatant *>
    getCombatantsAffectedBySphereAoE(const Combatant *caster, SpellTarget targetTemplate, SpellType abilityType, const Coord &origin) const;
    std::vector<Combatant *>
    getCombatantsAffectedByConeAoE(const Combatant *caster, SpellTarget targetTemplate, const Coord &origin, double angle) const;
    std::vector<Combatant *> getCombatantsAffectedByLineAoE(const Combatant *caster, const Coord &origin, double angle, int length, int width) const;
    std::vector<Combatant *> getCombatantsAffectedByBoxAoE(SpellTarget targetTemplate, const Coord &origin) const;
    Visibility getVisibility(const Coords &observer, const Coords &target);
    std::unordered_map<const Combatant *, Visibility> calcVisibilityDict(const Combatant *combatant, const Coord &theoreticalRootCoord);
    void calcVisibilityDictForAllCoords(const Combatant *combatant, const blaze::DynamicMatrix<Coord> &shortestPaths);
    Visibility getVisibilityFromCoord(const Coord &fromCoord, const Combatant * target) const;
    const std::unordered_map<Coord, std::unordered_map<const Combatant *, Visibility>> &getVisibilityDictForAllCoords() const
    {
      return _visibilityDictForAllCoords;
    }
    std::vector<Combatant*> getNonSwallowedEnemiesWithinRadius(const Combatant* combatant, int radius);
    std::vector<Combatant*> getNonSwallowedAlliesWithinRadius(const Combatant* combatant, int radius);
    std::vector<Combatant*> getNonSwallowedEnemiesWithinHopDistance(const Combatant* combatant, int distance);
    std::vector<Combatant*> getNonSwallowedEnemiesWithoutHopDistance(const Combatant* combatant, int distance);
    bool isDifficultTerrainAt(const Coords &coords) const;
    bool areEmptyOrSelf(const Coords &coords, const Combatant &combatant) const;
    void pushCombatantAwayFrom(const Vector2D &origin, Combatant *targetCombatant, int distance);
    void setCombatRound(uint32_t round);
    uint32_t getCombatRound();
    void withCombatantPosition(Combatant* combatant, const Coord& temporaryPosition, const std::function<void()>& fn);
    void withCombatantWildshapeReplacement(Actoid &actoid, Combatant *combatant, const Coord &origCoords, const std::function<void(bool)> &fn);
    // Convenience wrapper: applies the wildshape replacement (if the action belongs to a wildshaped form) for the
    // duration of fn() and exposes whether a transform is active via isWildshapeActive(). Mirrors the Python
    // `with replace_combatant_if_action_by_wildshaped(...) as did_transform` block.
    void withWildshapeIfNeeded(const std::shared_ptr<Actoid> &action, Combatant *combatant, const Coord &origCoords, const std::function<void()> &fn);
    bool isWildshapeActive() const { return _wildshapeActive; }
    std::optional<Coord> findWildshapedCoordinate(const Combatant *combatant, Size size, const std::optional<Coord> &origCoords = std::nullopt);
    std::vector<Combatant*> getPamEligibleCombatants(Combatant* combatant, const Coord& increment) const;
    std::vector<Combatant*> getAooEligibleCombatants(Combatant* combatant, const Coord& increment) const;

  private:
    size_t _size;
    MapMatrix _combatantGrid;
    MapMatrix _terrainGrid;
    MapMatrix _baseAdjacencyMatrix;
    // blaze::DynamicMatrix<int> _occupancyGrid TODO: This may actually not be needed
    std::unordered_map<int, Coords> _combatantCoordinateCache;
    // thread_local: each worker thread gets its own independent BattleMap so simulations can run in
    // parallel without sharing the (mutable, non-thread-safe) singleton state.
    static thread_local std::unique_ptr<BattleMap> _instance;
    std::unordered_set<Coord> _impassableSet;
    std::unordered_set<Coord> _difficultSet;
    std::vector<Obstacle> _obstacles;
    // std::unordered_map<std::pair<int, int>, std::unordered_map<const Combatant*, Visibility>, PairHash> _visibilityDictForAllCoords;
    std::unordered_map<Coord, std::unordered_map<const Combatant*, Visibility>> _visibilityDictForAllCoords;
    uint32_t _combatRound = 0U; // this isn't the best place for it
    bool _wildshapeActive = false; // true while a withWildshapeIfNeeded() callback runs against a transformed form


    BattleMap(size_t size);
    BattleMap(const BattleMap &) = delete;
    BattleMap &operator=(const BattleMap &) = delete;

    bool isEmptyOrSelf(int x, int y, int combatantId) const;
    void fillRegion(MapMatrix &mask, const Coord &coord, int offset, int value);
    blaze::StaticMatrix<int, 2, 2> getHarmfulBoundingBox(const Combatant *caster, int inflation);
  };
}
