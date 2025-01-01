#include "spells/spike_growth.hpp"

namespace enc
{

  size_t SpikeGrowth::hash() const
  {
    size_t h = std::hash<int>{}(static_cast<int>(getAbilityType()));
    h ^= std::hash<int>{}(static_cast<int>(getFlags())) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_coord[0]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_coord[1]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    return h;
  }

  bool SpikeGrowth::equals(const Actoid &other) const
  {
    if(auto *spikeGrowth = dynamic_cast<const SpikeGrowth *>(&other))
      {
        return getAbilityType() == other.getAbilityType() && getFlags() == other.getFlags() && _coord == spikeGrowth->_coord;
      }
    return false;
  }

} // namespace enc
