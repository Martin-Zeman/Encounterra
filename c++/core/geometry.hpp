#pragma once

#include <blaze/Math.h>
#include <vector>
#include <random>
#include <set>
#include "types.hpp"
#include "coords.hpp"

namespace enc
{
  double getCartesianDistanceCoords(const Coords &coords1, const Coords &coords2);

  int getHopDistanceCoords(const Coords &coords1, const Coords &coords2);

  blaze::DynamicMatrix<double> distanceMatrix(const Coords &coords1, const Coords &coords2);

  std::vector<Coord> inflateCoords(const Coords &coords, int inflate_to_dist);

  blaze::DynamicVector<double> linspace(double start, double end, size_t num);

  blaze::StaticVector<double, 3> cross(const blaze::StaticVector<double, 3> &a, const blaze::StaticVector<double, 3> &b);

  int randomInt(int min, int max);

  std::vector<Coord> convertPathToIncrements(const std::vector<Coord> &path);

  std::pair<double, double> linearRegression(const std::vector<std::array<double, 2>> &enemyPositions);

  std::vector<Coord> samplePointsOnLine(double m, double c, int gridSize, int numSamples = 20);

  double getAngleFromSlope(double m);

  blaze::StaticVector<double, 2> getSquareCenter(const Coord &coord);

  std::set<Coord> getAffectedByCone(const Coord &origin, double angleDeg, int radius, int gridSize);

}
