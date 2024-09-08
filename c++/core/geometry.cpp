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

  double cross(const Vector2D &a, const Vector2D &b)
  {
    return a[0] * b[1] - a[1] * b[0];
  };

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

  std::pair<double, double> linearRegression(const std::vector<Vector2D> &enemyPositions)
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
    column(A, 1) = blaze::DynamicVector<double>(n, 1.0); // Ensuring a column of ones

    // Solve the normal equation: (A^T * A) * result = A^T * y
    blaze::DynamicMatrix<double> ATA = blaze::trans(A) * A;
    blaze::DynamicVector<double> ATy = blaze::trans(A) * y;

    blaze::DynamicVector<double> result(2);
    solve(ATA, result, ATy);

    return {result[0], result[1]}; // m, c
  }


  std::vector<Vector2D> samplePointsOnLine(double m, double c, int gridSize, int numSamples)
  {
    std::vector<Vector2D> points;
    points.reserve(numSamples);

    double step = (gridSize - 1.0) / (numSamples - 1);
    for(int i = 0; i < numSamples; ++i)
      {
        double x = i * step;
        double y = m * x + c;
        points.push_back({x, y});
      }

    return points;
  }

  double getAngleFromSlope(double m) { return std::atan(m) * 180.0 / M_PI; }

  Vector2D getSquareCenter(const Coord &coord) { return {coord[0] + 0.5, coord[1] + 0.5}; }

  std::set<Coord> getAffectedByCone(const Coord &origin, double angleDeg, int radius, int gridSize)
  {
    Vector2D originCenter = getSquareCenter(origin);

    auto lineIncrement = [&originCenter, radius](double angle) {
      return Vector2D{originCenter[0] + radius * std::sin(angle), originCenter[1] + radius * std::cos(angle)};
    };

    auto polarity = [&originCenter](const Vector2D &linePoint, const Vector2D &queryPoint) {
      blaze::StaticMatrix<double, 2, 2> mat;
      column(mat, 0) = linePoint - originCenter;
      column(mat, 1) = queryPoint - originCenter;
      return blaze::det(mat);
    };

    double firstAngleRad = (angleDeg - 30) * M_PI / 180.0;
    Vector2D firstLinePoint = lineIncrement(firstAngleRad);

    double secondAngleRad = (angleDeg + 30) * M_PI / 180.0;
    Vector2D secondLinePoint = lineIncrement(secondAngleRad);

    std::set<Coord> coords;
    for(int x = 0; x < gridSize; ++x)
      {
        for(int y = 0; y < gridSize; ++y)
          {
            Vector2D currCoordCenter = getSquareCenter({x, y});
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

  std::set<Coord> getAffectedByLine(const Coord &origin, double angleDeg, double length, double width, int gridSize)
  {
    Vector2D originCenter = getSquareCenter(origin);
    double halfWidth = width / 2.0;

    double angleRad = angleDeg * M_PI / 180.0;
    Vector2D directionVector = {std::sin(angleRad), std::cos(angleRad)};

    Vector2D perpendicularVector = {-directionVector[1], directionVector[0]};

    std::set<Coord> coords;

    for(int x = 0; x < gridSize; ++x)
      {
        for(int y = 0; y < gridSize; ++y)
          {
            Vector2D currCoordCenter = getSquareCenter({x, y});
            Vector2D vectorToCoord = {currCoordCenter[0] - originCenter[0], currCoordCenter[1] - originCenter[1]};

            double distanceAlongLine = vectorToCoord[0] * directionVector[0] + vectorToCoord[1] * directionVector[1];

            if(0 <= distanceAlongLine && distanceAlongLine <= length)
              {
                double distancePerpendicular = std::abs(vectorToCoord[0] * perpendicularVector[0] + vectorToCoord[1] * perpendicularVector[1]);

                if(distancePerpendicular <= halfWidth)
                  {
                    coords.insert({x, y});
                  }
              }
          }
      }

    // coords.erase(origin);
    return coords;
  }

  std::vector<Coord> getCoordsAffectedBySquareAoE(const Coord &origin, int length, int gridSize)
  {
    std::vector<Coord> coords;
    coords.reserve(length * length);

    for(int i = 0; i < length; ++i)
      {
        for(int j = 0; j < length; ++j)
          {
            int x = origin[0] + i;
            int y = origin[1] + j;

            if(x < 0 || x >= gridSize || y < 0 || y >= gridSize)
              {
                continue;
              }

            coords.push_back({x, y});
          }
      }

    return coords;
  }

  /**
   * @brief Calculates the field of view vector from right and leftmost points of a target from the perspective of the observer
   * @param observer observer coordinates
   * @param target target coordinates
   * @return normalized vectors to the left and right most points from the observer's perspective ordered in counter-clockwise manner
   * (using the convex angle they define)
   */
  std::pair<Vector2D, Vector2D> findFovVectors(const Rectangle &observer, const Rectangle &target)
  {
    auto observer_center = observer.getCenter();
    auto target_center = target.getCenter();

    std::vector<std::pair<Vector2D, double>> vectors;
    for(const auto &corner : target.getCorners())
      {
        Vector2D corner_vec = {static_cast<double>(corner[0]), static_cast<double>(corner[1])};
        Vector2D vec = corner_vec - observer_center;
        Vector2D target_vec = target_center - observer_center;
        double angle = std::acos(blaze::dot(vec, target_vec) / (blaze::length(vec) * blaze::length(target_vec)));
        vectors.emplace_back(vec, angle);
      }

    std::sort(vectors.begin(), vectors.end(), [](const auto &a, const auto &b) { return a.second > b.second; });

    assert(vectors.size() > 1);

    auto normalize = [](const Vector2D &v) { return v / blaze::length(v); };

    if(vectors[0].first[0] * vectors[1].first[1] - vectors[0].first[1] * vectors[1].first[0] > 0)
      {
        return {normalize(vectors[0].first), normalize(vectors[1].first)};
      }
    return {normalize(vectors[1].first), normalize(vectors[0].first)};
  }

  /**
   * Calculates a bounding box which encloses both combatants
   * @param combatant1 Vector of coordinates for the first combatant
   * @param combatant2 Vector of coordinates for the second combatant
   * @return std::pair of bottom left corner and top right corner
   */
  std::pair<Coord, Coord> getBoundingBox(const CoordVector &combatant1, const CoordVector &combatant2)
  {
    if(combatant1.empty() || combatant2.empty())
      {
        throw std::invalid_argument("Combatant coordinates cannot be empty");
      }

    // Initialize min and max values with the first point of combatant1
    int min_x = combatant1[0][0];
    int min_y = combatant1[0][1];
    int max_x = combatant1[0][0];
    int max_y = combatant1[0][1];

    // Lambda function to update min and max
    auto update_bounds = [&](const Coord &coord) {
      min_x = std::min(min_x, coord[0]);
      min_y = std::min(min_y, coord[1]);
      max_x = std::max(max_x, coord[0]);
      max_y = std::max(max_y, coord[1]);
    };

    // Compute min and max for combatant1
    for(const auto &coord : combatant1)
      {
        update_bounds(coord);
      }

    // Compute min and max for combatant2
    for(const auto &coord : combatant2)
      {
        update_bounds(coord);
      }

    Coord bottom_left{min_x, min_y};
    Coord top_right{max_x, max_y};

    return {bottom_left, top_right};
  }

  /**
   * @brief Find the nearest valid grid coordinate to targetCoords from initCoords,
   *        ensuring the Chebyshev distance does not exceed maxDistance.
   *
   * This function starts searching from maxDistance, moving towards the target if necessary.
   * It uses the Chebyshev distance metric and Euclidean distance for sorting potential points.
   *
   * @param targetCoords The target coordinates as a Vector2D (blaze::StaticVector<double, 2UL>).
   * @param initCoords The initial coordinates as a Coord (std::array<int, 2>).
   * @param maxDistance The maximum allowed Chebyshev distance.
   * @return The adjusted coordinates as a Coord if within maxDistance, else initCoords.
   */
  Coord findNearestValidCoordinateChebyshev(const Vector2D &targetCoords, const Coord &initCoords, int maxDistance)
  {
    // Directly check if the rounded target is within the allowed distance first
    Coord roundedCoords = {static_cast<int>(std::round(targetCoords[0])), static_cast<int>(std::round(targetCoords[1]))};

    auto chebyshevDistance = [](const Coord &a, const Coord &b) { return std::max(std::abs(a[0] - b[0]), std::abs(a[1] - b[1])); };

    if(chebyshevDistance(roundedCoords, initCoords) <= maxDistance)
      {
        return roundedCoords;
      }

    // Start from the maximum distance and move inward
    for(int d = maxDistance; d > 1; --d)
      {
        // Explore the perimeter of the square defined by the Chebyshev distance d
        std::vector<Coord> potentialPoints = {{initCoords[0] + d, initCoords[1] + d},        {initCoords[0] + d + 1, initCoords[1] + d},
                                              {initCoords[0] + d, initCoords[1] + d + 1},    {initCoords[0] + d - 1, initCoords[1] + d},
                                              {initCoords[0] + d, initCoords[1] + d - 1},    {initCoords[0] + d + 1, initCoords[1] + d + 1},
                                              {initCoords[0] + d - 1, initCoords[1] + d - 1}};

        // Filter points based on Chebyshev distance
        potentialPoints.erase(
          std::remove_if(potentialPoints.begin(), potentialPoints.end(),
                         [&initCoords, d, &chebyshevDistance](const Coord &point) { return chebyshevDistance(point, initCoords) != d; }),
          potentialPoints.end());

        std::sort(potentialPoints.begin(), potentialPoints.end(),
                  [&targetCoords](const Coord &a, const Coord &b) { return euclidean(targetCoords, a) < euclidean(targetCoords, b); });

        if(!potentialPoints.empty())
          {
            return potentialPoints[0];
          }
      }

    // If no valid coordinate is found within the constraints, return the initial coordinates
    return initCoords;
  }
}
