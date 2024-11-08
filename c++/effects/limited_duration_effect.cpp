#include "effects/limited_duration_effect.hpp"

namespace enc
{
  bool LimitedDurationEffect::startOfTurnTick()
  {
    _turns--;
    return _turns > 0; // Return false if effect expired, true otherwise
  }
}
