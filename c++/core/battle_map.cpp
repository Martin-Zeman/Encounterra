#include "battle_map.hpp"
#include "geometry.hpp"
#include "teams.hpp"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <queue>
#include <set>

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

  bool BattleMap::isEmptyOrSelf(int x, int y, int combatantId) const
  {
    return (_combatantGrid(x, y) == -1 && _terrainGrid(x, y) != static_cast<int>(Terrain::IMPASSABLE_TERRAIN))
           || (_combatantGrid(x, y) != -1 && _combatantGrid(x, y) == combatantId);
  }

  size_t BattleMap::getGridSize() const { return _size; }

  void BattleMap::buildBaseAdjacencyMatrix()
  {
    int N = _size;
    int Nsq = N * N;

    // Initialize base_adjacency_matrix with zeros
    _baseAdjacencyMatrix.resize(Nsq, Nsq);
    _baseAdjacencyMatrix = 0;

    // Connect the nodes
    for(int i = 0; i < N; ++i)
      {
        for(int j = 0; j < N; ++j)
          {
            int idx = i * N + j;
            _baseAdjacencyMatrix(idx, std::max(i - 1, 0) * N + std::max(j - 1, 0)) = 1;
            _baseAdjacencyMatrix(idx, std::max(i - 1, 0) * N + j) = 1;
            _baseAdjacencyMatrix(idx, std::max(i - 1, 0) * N + std::min(j + 1, N - 1)) = 1;

            _baseAdjacencyMatrix(idx, i * N + std::max(j - 1, 0)) = 1;
            _baseAdjacencyMatrix(idx, i * N + j) = 1;
            _baseAdjacencyMatrix(idx, i * N + std::min(j + 1, N - 1)) = 1;

            _baseAdjacencyMatrix(idx, std::min(i + 1, N - 1) * N + std::max(j - 1, 0)) = 1;
            _baseAdjacencyMatrix(idx, std::min(i + 1, N - 1) * N + j) = 1;
            _baseAdjacencyMatrix(idx, std::min(i + 1, N - 1) * N + std::min(j + 1, N - 1)) = 1;
          }
      }

    // Remove self-connections
    for(int i = 0; i < Nsq; ++i)
      {
        _baseAdjacencyMatrix(i, i) = 0;
      }

    // Handle difficult set
    for(const auto &coord : _difficultSet)
      {
        int idx = coord[0] * N + coord[1];
        blaze::column(_baseAdjacencyMatrix, idx) *= 2;
      }

    // Handle impassable set
    for(const auto &coord : _impassableSet)
      {
        int idx = coord[0] * N + coord[1];
        blaze::column(_baseAdjacencyMatrix, idx) = 0;
      }
  }

  void BattleMap::fillRegion(MapMatrix &mask, const Coord &coord, int offset, int value)
  {
    int start_x = std::max(0, coord[0] - offset);
    int start_y = std::max(0, coord[1] - offset);
    int end_x = std::min(_size, static_cast<size_t>(coord[0] + 1));
    int end_y = std::min(_size, static_cast<size_t>(coord[1] + 1));

    for(int x = start_x; x < end_x; ++x)
      {
        for(int y = start_y; y < end_y; ++y)
          {
            for(int i = 0; i < _size * _size; ++i)
              {
                mask(i, x * _size + y) = value;
              }
          }
      }
  }

  MapMatrix BattleMap::buildCombatantAdjacencyMask(const Combatant &combatant, bool consider_aoo)
  {
    const int N = _size;
    Teams &teams = Teams::getInstance();

    int offset = 0;
    if(combatant.getSize() > Size::MEDIUM)
      {
        offset = static_cast<int>(combatant.getSize());
      }

    MapMatrix mask(N * N, N * N, 1);

    // Handle impassable terrain and other combatants
    for(const auto &[currCombatantId, coords] : _combatantCoordinateCache)
      {
        if(currCombatantId != combatant._id && teams.getCombatantById(currCombatantId)->isAlive())
          {
            for(const auto &coord : coords.get())
              {
                fillRegion(mask, coord, offset, 0);
              }
          }
      }
    for(const auto &coord : _impassableSet)
      {
        fillRegion(mask, coord, offset, 0);
      }

    // Handle AoO
    if(consider_aoo)
      {
        auto enemies = teams.getEnemies(combatant);
        for(const auto &e : enemies)
          {
            if(!e->hasReaction())
              {
                continue;
              }
            int rng = e->getMeleeReactionRange();
            auto coords = getCombatantCoordinates(*e);
            auto adj_coords = getFreeCoordsInHopRange(coords, blaze::DynamicVector<double>(), combatant.getSize(), rng);
            for(const auto &ac : adj_coords)
              {
                for(int i = 0; i < N * N; ++i)
                  {
                    mask(ac[0] * N + ac[1], i) *= 2;
                  }
              }
          }
      }

    // Handle map edges for larger combatants
    for(int i = (N - offset) * N; i < N * N; ++i)
      {
        for(int j = 0; j < N * N; ++j)
          {
            mask(i, j) = 0;
            mask(j, i) = 0;
          }
      }

    // TODO: Handle frightened condition
    // auto frightened_source = get_source_of_frightened(combatant);
    // if(frightened_source && frightened_source->is_alive())
    //   {
    //     auto source_coords = _combatantCoordinateCache.at(frightened_source->_id);
    //     int current_hop_distance = getHopDistanceCombatants(combatant, *frightened_source);

    //     for(int x = 0; x < N; ++x)
    //       {
    //         for(int y = 0; y < N; ++y)
    //           {
    //             int hop_distance = getHopDistanceCoords({{x, y}}, source_coords);
    //             if(hop_distance < current_hop_distance)
    //               {
    //                 for(int i = 0; i < N * N; ++i)
    //                   {
    //                     mask(i, x * N + y) = 0;
    //                   }
    //               }
    //           }
    //       }
    //   }

    return mask;
  }

  DijkstraResult BattleMap::dijkstra(const Coord &src, const MapMatrix &adjMatrix, const MapMatrix &mask)
  {
    const int N = _size;
    const int Nsq = N * N;
    const int maxsize = std::numeric_limits<int>::max();

    blaze::DynamicVector<int64_t> dist(Nsq, maxsize);
    int srcIdx = src[0] * N + src[1];
    dist[srcIdx] = 0;

    std::vector<bool> openSet(Nsq, false);

    // Element-wise multiplication of adjMatrix and mask
    blaze::DynamicMatrix<int64_t> adj = adjMatrix % mask;

    std::priority_queue<std::pair<int, int>, std::vector<std::pair<int, int>>, std::greater<std::pair<int, int>>> pq;
    pq.push({0, srcIdx});

    blaze::DynamicMatrix<Coord> shortestPaths(N, N, Coord{-1, -1});

    while(!pq.empty())
      {
        auto [current_dist, x] = pq.top();
        pq.pop();

        if(openSet[x])
          continue;
        openSet[x] = true;

        int fromX = x / N;
        int fromY = x % N;

        for(int y = 0; y < Nsq; ++y)
          {
            if(adj(x, y) > 0 && !openSet[y])
              {
                int toX = y / N;
                int toY = y % N;
                int newDist = dist[x] + adj(x, y);

                if(dist[y] > newDist)
                  {
                    dist[y] = newDist;
                    // shortestPaths(toX, toY) = Coord{fromX, fromY};
                    shortestPaths(toX, toY) = {fromX, fromY};
                    pq.push({newDist, y});
                  }
                else if(dist[y] == newDist)
                  {
                    // Check for the least zig-zaggy path
                    int current_path_diff = abs(shortestPaths(toX, toY)[0] - toX) + abs(shortestPaths(toX, toY)[1] - toY);
                    int new_path_diff = abs(toX - fromX) + abs(toY - fromY);
                    if(current_path_diff > new_path_diff)
                      {
                        // shortestPaths(toX, toY) = Coord{fromX, fromY};
                        shortestPaths(toX, toY) = {fromX, fromY};
                        pq.push({newDist, y});
                      }
                  }
              }
          }
      }

    return {dist, shortestPaths};
  }

  DijkstraResult BattleMap::calcDijkstra(const Combatant &combatant)
  {
    Coord coord = _combatantCoordinateCache.at(combatant._id).get()[0];
    auto mask = buildCombatantAdjacencyMask(combatant);
    return dijkstra(coord, _baseAdjacencyMatrix, mask);
  }

  std::vector<Coord>
  BattleMap::reconstructFromShortestPath(const blaze::DynamicMatrix<Coord> &shortest_paths, const Coord &source, const Coord &target)
  {
    size_t max_path_length = shortest_paths.rows() * shortest_paths.columns();
    std::vector<Coord> path;
    path.reserve(max_path_length);

    Coord current = target;

    while(current != source)
      {
        path.push_back(current);
        current = shortest_paths(current[0], current[1]);

        if(current[0] == -1 && current[1] == -1)
          {
            return std::vector<Coord>(); // Return an empty vector if no path is found
          }
      }

    path.push_back(source);
    std::reverse(path.begin(), path.end());

    return path;
  }

  int BattleMap::getHopDistanceCombatants(const Combatant &combatant1, const Combatant &combatant2) const
  {
    return getHopDistanceCoords(_combatantCoordinateCache.at(combatant1._id), _combatantCoordinateCache.at(combatant2._id));
  }

  std::optional<Coord> BattleMap::getNearestFreeAdjacentCoords(const Combatant &combatant, const Coords &myLocation, Size combatantSize,
                                                               const Coords &targetLocation, const blaze::DynamicVector<int> &distances, int rng)
  {
    std::vector<Coord> adjacentCoords = getFreeCoordsInHopRange(targetLocation, distances, combatantSize, rng, combatant._id);

    if(adjacentCoords.empty())
      {
        return std::nullopt;
      }

    // Sort adjacent coords based on Cartesian distance to myLocation
    std::sort(adjacentCoords.begin(), adjacentCoords.end(), [&myLocation](const Coord &a, const Coord &b) {
      return getCartesianDistanceCoords(a, myLocation.get()[0]) < getCartesianDistanceCoords(b, myLocation.get()[0]);
    });

    return adjacentCoords[0];
  }

  std::optional<std::vector<Coord>> BattleMap::getPathToCombatant(const Combatant& combatant, const Combatant& target,
                                                         const blaze::DynamicVector<int>& distances,
                                                         const blaze::DynamicMatrix<Coord>& shortestPaths,
                                                         int rng, bool considerAOO)
    {
        Coords myLocation = getCombatantCoordinates(combatant);
        Coord myCoord = myLocation.get()[0];
        // spdlog::debug("Origin {}", myCoord);

        Coords enemyLocation = getCombatantCoordinates(target);
        // spdlog::debug("Destination {}", enemyLocation.get()[0]);

        DijkstraResult dijkstraResult;
        if (distances.size() == 0 || shortestPaths.rows() == 0)
        {
            auto mask = buildCombatantAdjacencyMask(combatant, considerAOO);
            dijkstraResult = dijkstra(myCoord, _baseAdjacencyMatrix, mask);
        }
        else
        {
            dijkstraResult.dist = distances;
            dijkstraResult.shortestPaths = shortestPaths;
        }

        auto enemyAdjacentLocation = getNearestFreeAdjacentCoords(combatant, myLocation, combatant.getSize(), enemyLocation, dijkstraResult.dist, rng);
        if (!enemyAdjacentLocation)
        {
            return std::nullopt;
        }

        auto path = reconstructFromShortestPath(dijkstraResult.shortestPaths, myCoord, *enemyAdjacentLocation);
        if (path.empty())
        {
            return std::nullopt;
        }

        // if (spdlog::get_level() <= spdlog::level::info)
        // {
        //     printDijkstra(dijkstraResult.dist, myLocation, enemyLocation.get());
        // }

        return convertPathToIncrements(path);
    }

    std::optional<std::vector<Coord>> BattleMap::getPathToCoord(const Combatant& combatant, const Coord& targetCoord,
                                                     const blaze::DynamicVector<int>& distances,
                                                     const blaze::DynamicMatrix<Coord>& shortestPaths,
                                                     bool considerAOO)
    {
        Coords myLocation = getCombatantCoordinates(combatant);
        Coord myCoord = myLocation.get()[0];
        // spdlog::debug("Origin {}", myCoord);
        // spdlog::debug("Destination {}", targetCoord);

        DijkstraResult dijkstraResult;
        if (distances.size() == 0 || shortestPaths.rows() == 0)
        {
            auto mask = buildCombatantAdjacencyMask(combatant, considerAOO);
            dijkstraResult = dijkstra(myCoord, _baseAdjacencyMatrix, mask);
        }
        else
        {
            dijkstraResult.dist = distances;
            dijkstraResult.shortestPaths = shortestPaths;
        }

        auto path = reconstructFromShortestPath(dijkstraResult.shortestPaths, myCoord, targetCoord);
        if (path.empty())
        {
            return std::nullopt;
        }

        // if (spdlog::get_level() <= spdlog::level::info)
        // {
        //     printDijkstra(dijkstraResult.dist, myLocation, std::vector<Coord>{targetCoord});
        // }

        return convertPathToIncrements(path);
    }

  std::vector<Coord> BattleMap::getFreeCoordsInHopRange(const Coords &target, const blaze::DynamicVector<double> &distances, Size moverSize, int rng,
                                                        int combatantId) const
  {
    assert(rng > 0);
    auto inflated = inflateCoords(target, static_cast<int>(moverSize));
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

                if(isEmptyOrSelf(x, y, combatantId) && consider_accessibility)
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

  std::vector<Coord> BattleMap::getFreeCoordsInCartesianRange(const Coords &target, const blaze::DynamicVector<double> &distances, Size moverSize,
                                                              int rng, int combatantId) const
  {
    assert(rng > 0);
    auto inflated = inflateCoords(target, static_cast<int>(moverSize));
    std::unordered_set<Coord> coords_in_range;

    for(const auto &coord : inflated)
      {
        for(int i = -rng; i <= rng; ++i)
          {
            for(int j = -rng; j <= rng; ++j)
              {
                int x = coord[0] + i;
                int y = coord[1] + j;

                if(x < 0 || x >= static_cast<int>(_size) || y < 0 || y >= static_cast<int>(_size)
                   || getCartesianDistanceCoords(target, Coords(Coord{x, y}, Size::MEDIUM)) > rng)
                  {
                    continue;
                  }

                bool consider_accessibility = distances.size() > 0 ? distances[x * _size + y] < std::numeric_limits<double>::max() : true;

                if(isEmptyOrSelf(x, y, combatantId) && consider_accessibility)
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

  void BattleMap::moveCombatantByIncrement(const Combatant &combatant, const Coord &increment)
  {
    const auto &oldCoords = _combatantCoordinateCache.at(combatant._id);
    for(const auto &[x, y] : oldCoords.get())
      {
        _combatantGrid(x, y) = -1;
      }

    Coords newCoords(oldCoords, increment);
    // Check bounds and update _combatantGrid for new coordinates
    for(const auto &[x, y] : newCoords.get())
      {
        if(x >= _size || y >= _size || x < 0 || y < 0)
          {
            throw std::out_of_range("New coordinate out of bounds.");
          }
        _combatantGrid(x, y) = combatant._id;
      }

    _combatantCoordinateCache.insert_or_assign(combatant._id, std::move(newCoords));
  }

  void BattleMap::moveCombatant(const Combatant &combatant, const Coord &newCoord, bool log)
  {
    const auto &oldCoords = _combatantCoordinateCache.at(combatant._id);
    for(const auto &[x, y] : oldCoords.get())
      {
        _combatantGrid(x, y) = -1;
      }

    auto newCoords = Coords(newCoord, combatant);
    auto newCoordsData = newCoords.get();

    for(const auto &[x, y] : newCoordsData)
      {
        if(x >= _size || y >= _size || x < 0 || y < 0)
          {
            throw std::out_of_range("New coordinate out of bounds.");
          }
        _combatantGrid(x, y) = combatant._id;
      }

    _combatantCoordinateCache.insert_or_assign(combatant._id, std::move(newCoords));

    if(log)
      {
        // Assuming you have a logger, you can log the movement here
        // logger.info(combatant.name + " moved to (" + std::to_string(newCoordsData[0].first) + ", " + std::to_string(newCoordsData[0].second) + ")");
      }
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

  void BattleMap::removeCombatant(const Combatant& combatant) {
        auto it = _combatantCoordinateCache.find(combatant._id);
        if (it == _combatantCoordinateCache.end()) {
            return;  // already removed
        }
        
        const auto& oldCoords = it->second.get();
        for (const auto& coord : oldCoords) {
            _combatantGrid(coord[0], coord[1]) = -1;
            // _occupancyGrid(coord[0], coord[1]) = static_cast<int>(Occupancy::FREE);
        }
        
        _combatantCoordinateCache.erase(it);
    }

    bool BattleMap::removeCombatantIfDead(Combatant &combatant)
    {
      Combatant *targetToRemove = combatant.getOriginalForm();

      if(!targetToRemove->isAlive())
        {
          if(auto* grappler = targetToRemove->getInitiatorOfCondition(Conditions::GRAPPLED))
            {
              grappler->removeCondition(Conditions::GRAPPLING);
            }
          targetToRemove->onDie();
          // spdlog::info("{} died", targetToRemove.getName());
          removeCombatant(*targetToRemove);
          return false;
        }
      return true;
    }

    int BattleMap::getCombatantGridValueAt(const Coord &coord) { return _combatantGrid(coord[0], coord[1]); }

    blaze::StaticMatrix<int, 2, 2> BattleMap::getHarmfulBoundingBox(const Combatant *caster, int inflation)
    {
      blaze::StaticMatrix<int, 2, 2> bb = {{static_cast<int>(_size), static_cast<int>(_size)}, {0, 0}}; // top right, bottom left
      Teams &teams = Teams::getInstance();

      for(const auto &[combatantId, coords] : _combatantCoordinateCache)
        {
          const Combatant *combatant = teams.getCombatantById(combatantId);
          if(teams.areEnemies(*caster, *combatant))
            {
              const CoordVector &coordsVector = coords.get();
              for(const auto &coord : coordsVector)
                {
                  bb(0, 0) = std::min(bb(0, 0), coord[0]);
                  bb(0, 1) = std::min(bb(0, 1), coord[1]);
                  bb(1, 0) = std::max(bb(1, 0), coord[0]);
                  bb(1, 1) = std::max(bb(1, 1), coord[1]);
                }
            }
        }

      // Inflate the BB
      bb(0, 0) = std::max(bb(0, 0) - inflation, 0);
      bb(0, 1) = std::max(bb(0, 1) - inflation, 0);
      bb(1, 0) = std::min(bb(1, 0) + inflation, static_cast<int>(_size) - 1);
      bb(1, 1) = std::min(bb(1, 1) + inflation, static_cast<int>(_size) - 1);

      return bb;
    }

    std::tuple<Coord, int, std::vector<Combatant *>> BattleMap::findBestPlacementHarmfulCircular(const Combatant *caster, int spell_range, int radius)
    {
      auto bb = getHarmfulBoundingBox(caster, radius);
      int max_score = std::numeric_limits<int>::lowest();
      Coord best_placement{};
      std::vector<Combatant *> affected_combatants;
      Teams &teams = Teams::getInstance();

      const Combatant *swallower = caster->getSwallower();
      const Coords& caster_coords = swallower ? _combatantCoordinateCache.at(swallower->_id) : _combatantCoordinateCache.at(caster->_id);

      for(int x = bb(0, 0); x <= bb(1, 0); ++x)
        {
          for(int y = bb(0, 1); y <= bb(1, 1); ++y)
            {
              Coords curr_coords({x, y});

              auto dist = getCartesianDistanceCoords(caster_coords, curr_coords);
              if(dist > spell_range || dist <= radius)
                {
                  continue;
                }

              int score = 0;
              std::vector<Combatant *> affected;

              for(const auto &[combatantId, coords] : _combatantCoordinateCache)
                {
                  const Combatant *combatant = teams.getCombatantById(combatantId);
                  if(getCartesianDistanceCoords(coords, curr_coords) <= radius)
                    {
                      score += teams.areEnemies(*caster, *combatant) && combatant->isAlive() ? 1 : -4;
                      affected.push_back(const_cast<Combatant *>(combatant)); // Casting away constness, be cautious
                    }
                }

              if(score > max_score)
                {
                  max_score = score;
                  best_placement = curr_coords.get()[0];
                  affected_combatants = affected;
                }
            }
        }

      return {best_placement, max_score, affected_combatants};
    }

    std::tuple<Coord, int, std::vector<Combatant *>> BattleMap::findBestPlacementHarmfulSquare(const Combatant *caster, int spell_range, int length)
    {
      auto bb = getHarmfulBoundingBox(caster, length);
      int max_score = std::numeric_limits<int>::lowest();
      Coord best_placement{};
      std::vector<Combatant *> affected_combatants;
      Teams &teams = Teams::getInstance();

      const Coords &caster_coords = _combatantCoordinateCache.at(caster->_id);

      for(int x = bb(0, 0); x <= bb(1, 0); ++x)
        {
          for(int y = bb(0, 1); y <= bb(1, 1); ++y)
            {
              Coords curr_coords({x, y}, Size(length - 1));

              auto dist = getCartesianDistanceCoords(caster_coords, curr_coords);
              if(dist > spell_range || dist == 0) // TODO: is a 0 possible? Create a unit test for this case
                {
                  continue;
                }

              int score = 0;
              std::vector<Combatant *> affected;

              for(const auto &[combatantId, coords] : _combatantCoordinateCache)
                {
                  const Combatant *combatant = teams.getCombatantById(combatantId);
                  if(getCartesianDistanceCoords(coords, curr_coords) == 0)
                    {
                      score += teams.areEnemies(*caster, *combatant) && combatant->isAlive() ? 1 : -4;
                      affected.push_back(const_cast<Combatant *>(combatant)); // Casting away constness, be cautious
                    }
                }

              if(score > max_score)
                {
                  max_score = score;
                  best_placement = curr_coords.get()[0];
                  affected_combatants = affected;
                }
            }
        }

      if(best_placement[0] != 0 || best_placement[1] != 0)
        {
          return std::make_tuple(best_placement, max_score, affected_combatants);
        }
      return std::make_tuple(Coord{}, 0, std::vector<Combatant *>{});
    }

    std::pair<Coord, double> BattleMap::findBestPlacementHarmfulCone(const Combatant *caster, int radius)
    {
      std::vector<std::array<double, 2>> enemyPositions;
      Teams &teams = Teams::getInstance();
      for(Combatant *enemy : teams.getEnemies(*caster))
        {
          enemyPositions.push_back(_combatantCoordinateCache.at(enemy->_id).getCenter());
        }

      auto [m, c] = linearRegression(enemyPositions);
      double baseAngle = 90.0 - getAngleFromSlope(m);

      std::vector<double> angleRange;
      for(double angle = baseAngle - 15.0; angle <= baseAngle + 15.1; angle += 3.0)
        {
          angleRange.push_back(angle);
        }

      std::unordered_map<int, const Coords *> combatantIdsToCoords;
      std::set<Coord> allCombatantCoords;
      for(const auto &[combatantId, coords] : _combatantCoordinateCache)
        {
          if(combatantId != caster->_id)
            {
              combatantIdsToCoords[combatantId] = &coords;
              const auto &coordVec = coords.get();
              allCombatantCoords.insert(coordVec.begin(), coordVec.end());
            }
        }

      int maxScore = std::numeric_limits<int>::lowest();
      std::vector<std::pair<Coord, double>> bestPoses;

      for(double angle : angleRange)
        {
          auto samplePoints = samplePointsOnLine(std::tan(angle * M_PI / 180.0), c, _size);
          Coord lastOrigin = {-1, -1};
          for(const auto &point : samplePoints)
            {
              Coord origin = {point[0], point[1]};
              if(allCombatantCoords.find(origin) != allCombatantCoords.end())
                {
                  continue;
                }
              if(origin[0] >= 0 && origin[0] < _size && origin[1] >= 0 && origin[1] < _size && origin != lastOrigin)
                {
                  lastOrigin = origin;
                  for(double effectiveAngle : {angle, angle + 180.0})
                    {
                      int score = 0;
                      auto affectedCoords = getAffectedByCone(origin, effectiveAngle, radius, _size);
                      for(const auto &[combatantId, coords] : combatantIdsToCoords)
                        {
                          const auto &coordVec = coords->get();
                          if(std::any_of(coordVec.begin(), coordVec.end(),
                                         [&affectedCoords](const Coord &c) { return affectedCoords.find(c) != affectedCoords.end(); }))
                            {
                              if(combatantId == caster->_id)
                                continue;
                              Combatant *currCombatant = teams.getCombatantById(combatantId);
                              score += teams.areEnemies(*caster, *currCombatant) && currCombatant->isAlive() ? 1 : -4;
                            }
                        }
                      if(score > maxScore)
                        {
                          maxScore = score;
                          bestPoses = {{origin, effectiveAngle}};
                        }
                      else if(score == maxScore && score > 0)
                        {
                          bestPoses.push_back({origin, effectiveAngle});
                        }
                    }
                }
            }
        }

      if(bestPoses.empty())
        {
          return {{}, 0};
        }

      const Coords &casterPosition = getCombatantCoordinates(*caster);
      std::sort(bestPoses.begin(), bestPoses.end(), [this, &casterPosition](const auto &a, const auto &b) {
        return getHopDistanceCoords(casterPosition, Coords(a.first)) < getHopDistanceCoords(casterPosition, Coords(b.first));
      });

      return bestPoses[0];
    }
};
