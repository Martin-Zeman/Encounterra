#include "geometry.hpp"
#include "misc.hpp"
#include <cmath>

namespace enc {

blaze::DynamicMatrix<double> distanceMatrix(const blaze::DynamicMatrix<double> &coords1, const blaze::DynamicMatrix<double> &coords2)
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

std::vector<Coord> inflateCoords(const blaze::DynamicMatrix<double> &coords, int inflate_to_dist)
{
  int offset = 0;
  if(inflate_to_dist > static_cast<int>(Size::MEDIUM))
    {
      offset = inflate_to_dist;
    }

  std::vector<Coord> inflated;
  for(size_t i = 0; i < coords.rows(); ++i)
    {
      for(int x = static_cast<int>(coords(i, 0)) - offset; x <= coords(i, 0); ++x)
        {
          for(int y = static_cast<int>(coords(i, 1)) - offset; y <= coords(i, 1); ++y)
            {
              inflated.emplace_back(Coord{std::max(0, x), std::max(0, y)});
            }
        }
    }

  // Remove duplicates
  std::sort(inflated.begin(), inflated.end());
  inflated.erase(std::unique(inflated.begin(), inflated.end()), inflated.end());

  return inflated;
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
