#pragma once

#include <unordered_map>

namespace enc
{

  enum class SpellTarget
  {
    SELF,
    ONE_CREATURE,
    TWO_CREATURES,
    THREE_CREATURES,
    RADIUS_10,
    RADIUS_20,
    RADIUS_30,
    BOX_5,
    BOX_15,
    BOX_20,
    CONE_15,
    CONE_30,
    CONE_60,
    CONE_90
  };

  extern const std::unordered_map<SpellTarget, int> TRANSLATE_RADIUS;
  extern const std::unordered_map<SpellTarget, int> TRANSLATE_CONE;
  extern const std::unordered_map<SpellTarget, int> TRANSLATE_BOX;

  enum class SpellRange
  {
    SELF = -1,
    SIGHT = 0,
    TOUCH = 1,
    FEET_10 = 2,
    FEET_30 = 6,
    FEET_60 = 12,
    FEET_90 = 18,
    FEET_100 = 20,
    FEET_120 = 24,
    FEET_150 = 30,
    FEET_300 = 60
  };

  enum class Duration
  {
    UNLIMITED = -1,
    INSTANTANEOUS = 0,
    ROUND_ONE = 1,
    MINUTE = 10,
    TEN_MINUTES = 100
  };

  enum class Type
  {
    HARMFUL = 1,
    BUFF = 2,
    OTHER = 3
  };
}
