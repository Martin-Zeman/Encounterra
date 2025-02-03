#include "actions/break_grapple.hpp"

namespace enc
{

  BreakGrappleFactory::BreakGrappleFactory(Combatant *combatant)
      : ActoidFactory("BreakGrappleFactory", "Break Grapple", combatant, AbilityType::BREAK_GRAPPLE)
  {}

  Actoid *BreakGrappleFactory::create(void *target)
  {
    if(!target)
      {
        return nullptr;
      }
    return new BreakGrapple(*this, static_cast<ConditionWithDC *>(target));
  }

  BreakGrapple::BreakGrapple(BreakGrappleFactory &factory, ConditionWithDC *grappleCondition)
      : Actoid(factory, ActoidFlags::IS_BREAK_GRAPPLE, AbilityType::BREAK_GRAPPLE), _grappleCondition(grappleCondition)
  {}

  BreakGrapple::BreakGrapple(const BreakGrapple &other)
      : Actoid(const_cast<ActoidFactory &>(other._factory), static_cast<ActoidFlags>(other._actoidFlags), other._abilityType),
        _grappleCondition(other._grappleCondition)
  {}

} // namespace enc
