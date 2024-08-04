#pragma once

#include <array>
#include <vector>
#include <cstdint>
#include "types.hpp"

namespace enc{

class Obstacle {
public:
    Obstacle(const Coord& coord, int32_t radius = 0)
        : _coord(coord), _radius(radius) {}

    std::vector<std::array<int64_t, 2>> getCorners() const;

    std::array<double, 2> getCenter() const;

    const Coord& getCoord() const { return _coord; }
    int32_t getRadius() const { return _radius; }

private:
    Coord _coord;
    int32_t _radius;
};

}
