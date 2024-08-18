#include "geometry.hpp"
#include "misc.hpp"
#include <cmath>
#include <unordered_set>
#include <blaze/Math.h>

namespace enc
{

  double getCartesianDistanceCoords(const Coords &coords1, const Coords &coords2) { return blaze::min(distanceMatrix(coords1, coords2)); }

  int getHopDistanceCoords(const Coords &coords1, const Coords &coords2)
  {
    auto dist_mat = distanceMatrix(coords1, coords2);
    double min_dist = std::numeric_limits<double>::max();
    size_t min_row = 0, min_col = 0;

    for(size_t i = 0; i < dist_mat.rows(); ++i)
      {
        for(size_t j = 0; j < dist_mat.columns(); ++j)
          {
            if(dist_mat(i, j) < min_dist)
              {
                min_dist = dist_mat(i, j);
                min_row = i;
                min_col = j;
              }
          }
      }

    const auto &coords1_vec = coords1.get();
    const auto &coords2_vec = coords2.get();

    const Coord &sub1_closest_coord = coords1_vec[std::min(min_row, coords1_vec.size() - 1)];
    const Coord &sub2_closest_coord = coords2_vec[std::min(min_col, coords2_vec.size() - 1)];

    return std::max(std::abs(sub1_closest_coord[0] - sub2_closest_coord[0]), std::abs(sub1_closest_coord[1] - sub2_closest_coord[1]));
  }

  blaze::DynamicMatrix<double> distanceMatrix(const Coords &coords1, const Coords &coords2)
  {
    size_t n = coords1.numCoords();
    size_t m = coords2.numCoords();
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

  std::vector<Coord> convertPathToIncrements(const std::vector<Coord> &path)
  {
    std::vector<Coord> increments;
    increments.reserve(path.size() - 1);

    for(size_t i = 0; i < path.size() - 1; ++i)
      {
        Coord increment = {path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]};
        increments.push_back(increment);
      }

    return increments;
  }

  std::pair<double, double> linearRegression(const std::vector<std::array<double, 2>> &enemyPositions)
  {
    size_t n = enemyPositions.size();
    blaze::DynamicVector<double> x(n);
    blaze::DynamicVector<double> y(n);

    for(size_t i = 0; i < n; ++i)
      {
        x[i] = enemyPositions[i][0];
        y[i] = enemyPositions[i][1];
      }

    blaze::DynamicMatrix<double> A(n, 2);
    column(A, 0) = x;
    column(A, 1) = 1.0;

    // Solve the normal equation: (A^T * A) * result = A^T * y
    blaze::DynamicMatrix<double> ATA = blaze::trans(A) * A;
    blaze::DynamicVector<double> ATy = blaze::trans(A) * y;

    blaze::DynamicVector<double> result(2);
    solve(ATA, result, ATy);

    return {result[0], result[1]}; // m, c
  }

  std::vector<Coord> samplePointsOnLine(double m, double c, int gridSize, int numSamples)
  {
    std::vector<Coord> points;
    for(int i = 0; i < numSamples; ++i)
      {
        double x = i * (gridSize - 1.0) / (numSamples - 1);
        double y = m * x + c;
        points.push_back({static_cast<int>(std::round(x)), static_cast<int>(std::round(y))});
      }
    return points;
  }

  double getAngleFromSlope(double m) { return std::atan(m) * 180.0 / M_PI; }

  blaze::StaticVector<double, 2> getSquareCenter(const Coord &coord) { return {coord[0] + 0.5, coord[1] + 0.5}; }

  std::set<Coord> getAffectedByCone(const Coord &origin, double angleDeg, int radius, int gridSize)
  {
    blaze::StaticVector<double, 2> originCenter = getSquareCenter(origin);

    auto lineIncrement = [&originCenter, radius](double angle) {
      return blaze::StaticVector<double, 2>{originCenter[0] + radius * std::sin(angle), originCenter[1] + radius * std::cos(angle)};
    };

    auto polarity = [&originCenter](const blaze::StaticVector<double, 2> &linePoint, const blaze::StaticVector<double, 2> &queryPoint) {
      blaze::StaticMatrix<double, 2, 2> mat;
      column(mat, 0) = linePoint - originCenter;
      column(mat, 1) = queryPoint - originCenter;
      return blaze::det(mat);
    };

    double firstAngleRad = (angleDeg - 30) * M_PI / 180.0;
    blaze::StaticVector<double, 2> firstLinePoint = lineIncrement(firstAngleRad);

    double secondAngleRad = (angleDeg + 30) * M_PI / 180.0;
    blaze::StaticVector<double, 2> secondLinePoint = lineIncrement(secondAngleRad);

    std::set<Coord> coords;
    for(int x = 0; x < gridSize; ++x)
      {
        for(int y = 0; y < gridSize; ++y)
          {
            blaze::StaticVector<double, 2> currCoordCenter = getSquareCenter({x, y});
            if(blaze::length(originCenter - currCoordCenter) < radius && polarity(firstLinePoint, currCoordCenter) <= 0
               && polarity(secondLinePoint, currCoordCenter) >= 0)
              {
                coords.insert({x, y});
              }
          }
      }

    coords.erase(origin);

    // Approximation of > 1/2 of area covered for the corners of the cone
    if(std::fmod(firstLinePoint[0], 1.0) >= 0.5 || std::fmod(firstLinePoint[1], 1.0) <= 0.5)
      {
        coords.erase({static_cast<int>(std::floor(firstLinePoint[0])), static_cast<int>(std::floor(firstLinePoint[1]))});
      }
    if(std::fmod(secondLinePoint[0], 1.0) <= 0.5 || std::fmod(secondLinePoint[1], 1.0) <= 0.5)
      {
        coords.erase({static_cast<int>(std::floor(secondLinePoint[0])), static_cast<int>(std::floor(secondLinePoint[1]))});
      }

    return coords;
  }

}
