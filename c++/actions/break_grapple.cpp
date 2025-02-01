#include "actions/break_grapple.hpp"

namespace enc
{

  BreakGrappleFactory::BreakGrappleFactory(std::weak_ptr<ConditionWithDC> grappleCondition)
      : ActoidFactory("BreakGrappleFactory", "Break Grapple", nullptr, AbilityType::BREAK_GRAPPLE), _grappleCondition(grappleCondition)
  {}

  Actoid * BreakGrappleFactory::create(void *target) { return std::make_shared<BreakGrapple>(*this); }

  BreakGrapple::BreakGrapple(BreakGrappleFactory &factory) : Actoid(factory, ActoidFlags::IS_BREAK_GRAPPLE, AbilityType::BREAK_GRAPPLE) {}

} // namespace enc
