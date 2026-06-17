#include "actions/break_grapple.hpp"

namespace enc
{
  std::shared_ptr<Actoid> BreakGrappleFactory::create(void *target)
  {
    return std::make_shared<BreakGrapple>(*this);
  }
}
