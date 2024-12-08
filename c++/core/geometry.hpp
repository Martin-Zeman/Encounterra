#pragma once

#include <blaze/Math.h>
#include <cmath>
#include <vector>
#include <random>
#include <set>
#include "core/types.hpp"
#include "core/coords.hpp"

namespace enc
{
  double getCartesianDistanceCoords(const Coords &coords1, const Coords &coords2);

  int getHopDistanceCoords(const Coords &coords1, const Coords &coords2);

  blaze::DynamicMatrix<double> distanceMatrix(const Coords &coords1, const Coords &coords2);

  CoordVector inflateCoords(const Coords &coords, int inflate_to_dist);

  blaze::DynamicVector<double> linspace(double start, double end, size_t num);

  blaze::StaticVector<double, 3> cross(const blaze::StaticVector<double, 3> &a, const blaze::StaticVector<double, 3> &b);

  double cross(const Vector2D &a, const Vector2D &b);

  int randomInt(int min, int max);

  CoordVector convertPathToIncrements(const CoordVector &path);

  std::pair<double, double> linearRegression(const std::vector<Vector2D> &enemyPositions);

  std::vector<Vector2D> samplePointsOnLine(double m, double c, int gridSize, int numSamples = 20);

  double getAngleFromSlope(double m);

  Vector2D getSquareCenter(const Coord &coord);

  std::set<Coord> getAffectedByCone(const Coord &origin, double angleDeg, int radius, int gridSize);

  std::set<Coord> getAffectedByLine(const Coord &origin, double angleDeg, double length, double width, int gridSize);

  CoordVector getCoordsAffectedBySquareAoE(const Coord &origin, int length, int gridSize);

  std::pair<Vector2D, Vector2D> findFovVectors(const Rectangle &observer, const Rectangle &target);

  /**
   * Calculates the angle (in degrees) between two vectors
   * @param vector_1 The first vector
   * @param vector_2 The second vector
   * @return The convex angle (in degrees) formed by the two vectors.
   */
  template <typename VectorType> double angleBetweenVectors(const VectorType &vector_1, const VectorType &vector_2)
  {
    double dot_prod = blaze::dot(vector_1, vector_2);
    double mag_1 = blaze::length(vector_1);
    double mag_2 = blaze::length(vector_2);

    double cos_angle = std::max(-1.0, std::min(dot_prod / (mag_1 * mag_2), 1.0));
    double angle_rad = std::acos(cos_angle);
    double angle_deg = angle_rad * 180.0 / M_PI;

    angle_deg = std::fmod(angle_deg, 360.0);
    return (angle_deg - 180.0 < 0) ? angle_deg : 360.0 - angle_deg;
  }

  /**
   * Calculates the angle (in radians) between two vectors
   * @param vector_1 The first vector
   * @param vector_2 The second vector
   * @return The convex angle (in radians) formed by the two vectors.
   */
  template <typename VectorType> double angleBetweenVectorsRad(const VectorType &vector_1, const VectorType &vector_2)
  {
    double dot_prod = blaze::dot(vector_1, vector_2);
    double mag_1 = blaze::length(vector_1);
    double mag_2 = blaze::length(vector_2);

    double cos_angle = std::max(-1.0, std::min(dot_prod / (mag_1 * mag_2), 1.0));
    return std::acos(cos_angle);
  }

  std::pair<Coord, Coord> getBoundingBox(const CoordVector &combatant1, const CoordVector &combatant2);

  Coord findNearestValidCoordinateChebyshev(const Vector2D &targetCoords, const Coord &initCoords, int maxDistance);

  /**
   * @brief Calculate the Euclidean distance between two points.
   *
   * This function calculates the Euclidean distance between two points in 2D space.
   * It can handle both integer and floating-point coordinates.
   *
   * @tparam T The type of the coordinate components (int or double).
   * @param a The first point.
   * @param b The second point.
   * @return The Euclidean distance between the two points.
   */
  template <typename T> double euclidean(const Vector2D &a, const std::array<T, 2> &b)
  {
    double dx = static_cast<double>(a[0]) - static_cast<double>(b[0]);
    double dy = static_cast<double>(a[1]) - static_cast<double>(b[1]);
    return std::sqrt(dx * dx + dy * dy);
  }
}
