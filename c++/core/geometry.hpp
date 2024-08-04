#pragma once

#include <blaze/Math.h>
#include <vector>
#include <random>
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

}
