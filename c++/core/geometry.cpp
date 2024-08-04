#include "geometry.hpp"
#include "misc.hpp"
#include <cmath>
#include <unordered_set>

namespace enc {

blaze::DynamicMatrix<double> distanceMatrix(const Coords &coords1, const Coords &coords2)
{
  size_t n = coords1.rows();
  size_t m = coords2.rows();
  blaze::DynamicMatrix<double> distances(n, m);

  for(size_t i = 0; i < n; ++i)
    {
      for(size_t j = 0; j < m; ++j)
        {
          distances(i, j) = std::sqrt(std::pow(coords1(i, 0) - coords2(j, 0), 2) + std::pow(coords1(i, 1) - coords2(j, 1), 2));
        }
    }

  return distances;
}

std::vector<Coord> inflateCoords(const Coords &coords, int inflate_to_dist)
{
  int offset = 0;
  if(inflate_to_dist > static_cast<int>(Size::MEDIUM))
    {
      offset = inflate_to_dist;
    }

  std::unordered_set<Coord> inflated;
  for(const auto &[x, y] : coords.get())
    {
      for(int dx = -offset; dx <= offset; ++dx)
        {
          for(int dy = -offset; dy <= offset; ++dy)
            {
              int newX = std::max(0, x + dx);
              int newY = std::max(0, y + dy);
              inflated.insert({newX, newY});
            }
        }
    }

  return std::vector<Coord>(inflated.begin(), inflated.end());
}

blaze::DynamicVector<double> linspace(double start, double end, size_t num)
{
  blaze::DynamicVector<double> result(num);
  double step = (end - start) / (num - 1);
  for(size_t i = 0; i < num; ++i)
    {
      result[i] = start + i * step;
    }
  return result;
}

blaze::StaticVector<double, 3> cross(const blaze::StaticVector<double, 3> &a, const blaze::StaticVector<double, 3> &b)
{
  return blaze::StaticVector<double, 3>{a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
}

std::mt19937 rng(std::random_device{}());
int randomInt(int min, int max) { return std::uniform_int_distribution<int>{min, max}(rng); }

}
