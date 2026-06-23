#include "spell_stats.hpp"

namespace enc
{
  const std::unordered_map<SpellTarget, int> TRANSLATE_RADIUS
    = {{SpellTarget::RADIUS_5, 1}, {SpellTarget::RADIUS_10, 2}, {SpellTarget::RADIUS_20, 4}, {SpellTarget::RADIUS_30, 6}};

  const std::unordered_map<SpellTarget, int> TRANSLATE_CONE
    = {{SpellTarget::CONE_15, 3}, {SpellTarget::CONE_30, 6}, {SpellTarget::CONE_60, 12}, {SpellTarget::CONE_90, 18}};

  const std::unordered_map<SpellTarget, int> TRANSLATE_BOX 
    = {{SpellTarget::BOX_5, 1}, {SpellTarget::BOX_15, 3}, {SpellTarget::BOX_20, 4}};
}