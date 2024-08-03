#pragma once

#include <blaze/Math.h>
#include <array>

namespace enc {

using Coord = std::array<int, 2>;
using CoordVector = std::vector<Coord>;
using Die = blaze::StaticVector<uint8_t, 2>;

}
