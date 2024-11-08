#pragma once

#include <blaze/Math.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include <limits>
#include <random>
#include <stdexcept>
#include <optional>
#include "misc.hpp"
#include "types.hpp"
#include "coords.hpp"
#include "combatant.hpp"
#include "obstacle.hpp"
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

    std::vector<Coord> getFreeCoordsInHopRange(const Coords &target, const blaze::DynamicVector<double> &distances = blaze::DynamicVector<double>(),
                                               Size moverSize = Size::MEDIUM, int rng = 1, int combatantId = -1) const;

    std::vector<Coord> getFreeCoordsInCartesianRange(const Coords &target, const blaze::DynamicVector<double> &distances,
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
    std::vector<Coord> reconstructFromShortestPath(const blaze::DynamicMatrix<Coord> &shortest_paths, const Coord &source, const Coord &target);
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
    std::optional<std::vector<Coord>>
    getPathToCombatant(const Combatant &combatant, const Combatant &target, const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                       const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>(), int rng = 1, bool considerAOO = false);
    std::optional<std::vector<Coord>>
    getPathToCoord(const Combatant &combatant, const Coord &targetCoord, const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                   const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>(), bool considerAOO = false);
    void removeCombatant(const Combatant &combatant);
    bool removeCombatantIfDead(Combatant &combatant);
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
    std::vector<Combatant*> getNonSwallowedEnemiesWithinRadius(const Combatant* combatant, int radius);
    std::vector<Combatant*> getNonSwallowedAlliesWithinRadius(const Combatant* combatant, int radius);
    std::vector<Combatant*> getNonSwallowedEnemiesWithinHopDistance(const Combatant* combatant, int distance);
    std::vector<Combatant*> getNonSwallowedEnemiesWithoutHopDistance(const Combatant* combatant, int distance);
    bool isDifficultTerrainAt(const Coords &coords) const;
    void pushCombatantAwayFrom(const Vector2D &origin, Combatant *targetCombatant, int distance);

  private:
    size_t _size;
    MapMatrix _combatantGrid;
    MapMatrix _terrainGrid;
    MapMatrix _baseAdjacencyMatrix;
    // blaze::DynamicMatrix<int> _occupancyGrid TODO: This may actually not be needed
    std::unordered_map<int, Coords> _combatantCoordinateCache;
    static std::unique_ptr<BattleMap> _instance;
    std::unordered_set<Coord> _impassableSet;
    std::unordered_set<Coord> _difficultSet;
    std::vector<Obstacle> _obstacles;
    // std::unordered_map<std::pair<int, int>, std::unordered_map<const Combatant*, Visibility>, PairHash> _visibilityDictForAllCoords;
    std::unordered_map<Coord, std::unordered_map<const Combatant*, Visibility>> _visibilityDictForAllCoords;


    BattleMap(size_t size);
    BattleMap(const BattleMap &) = delete;
    BattleMap &operator=(const BattleMap &) = delete;

    bool isEmptyOrSelf(int x, int y, int combatantId) const;
    bool areEmptyOrSelf(const Coords &coords, const Combatant &combatant) const;
    void fillRegion(MapMatrix &mask, const Coord &coord, int offset, int value);
    blaze::StaticMatrix<int, 2, 2> getHarmfulBoundingBox(const Combatant *caster, int inflation);
  };
}
