#pragma once

#include <blaze/Math.h>
#include <vector>
#include <random>
#include "types.hpp"

namespace enc
{

  blaze::DynamicMatrix<double> distanceMatrix(const blaze::DynamicMatrix<double> &coords1, const blaze::DynamicMatrix<double> &coords2);

  std::vector<Coord> inflateCoords(const blaze::DynamicMatrix<double> &coords, int inflate_to_dist);

  blaze::DynamicVector<double> linspace(double start, double end, size_t num);

  blaze::StaticVector<double, 3> cross(const blaze::StaticVector<double, 3> &a, const blaze::StaticVector<double, 3> &b);

  int randomInt(int min, int max);

}
