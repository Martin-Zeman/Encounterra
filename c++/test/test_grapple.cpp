#include <gtest/gtest.h>
#include "core/combatant.hpp"
#include "core/conditions.hpp"
#include "core/misc.hpp"
#include "abilities/on_hit_grapple.hpp"
#include "combatants/bugbear_warrior.hpp"
#include "combatants/goblin.hpp"

using namespace enc;

namespace
{
  // Deterministic coverage of the 2024 grapple mechanics that do not depend on the d20 RNG.

  TEST(GrappleTest, OnHitGrappleAppliesGrappledAndGrappling)
  {
    BugbearWarrior grappler("Grappler");
    Goblin target(1);

    OnHitGrapple onHit(12, SkillCheck::ATHLETICS);
    onHit.hit(&grappler, nullptr, &target, 1.0, 0.0);

    EXPECT_TRUE(target.isAffectedBy(Conditions::GRAPPLED));
    EXPECT_TRUE(grappler.isAffectedBy(Conditions::GRAPPLING));
    // 2024 Grab applies only Grappled, not Restrained.
    EXPECT_FALSE(target.isAffectedBy(Conditions::RESTRAINED));
    EXPECT_EQ(target.getInitiatorOfCondition(Conditions::GRAPPLED), &grappler);
    EXPECT_EQ(grappler.getGrappledTarget(), &target);
  }

  TEST(GrappleTest, OnHitGrappleDoesNotOverwriteExistingGrapple)
  {
    BugbearWarrior first("First");
    BugbearWarrior second("Second");
    Goblin target(1);

    OnHitGrapple(12).hit(&first, nullptr, &target, 1.0, 0.0);
    OnHitGrapple(15).hit(&second, nullptr, &target, 1.0, 0.0);

    // A creature can be grappled by only one grappler: the first keeps the grapple, the second fails.
    EXPECT_EQ(target.getInitiatorOfCondition(Conditions::GRAPPLED), &first);
    EXPECT_FALSE(second.isAffectedBy(Conditions::GRAPPLING));
  }

  TEST(GrappleTest, BreakingOutOfGrappleEndsBothConditions)
  {
    BugbearWarrior grappler("Grappler");
    Goblin target(1);
    OnHitGrapple(12).hit(&grappler, nullptr, &target, 1.0, 0.0);
    ASSERT_TRUE(target.isAffectedBy(Conditions::GRAPPLED));

    grappler.removeCondition(Conditions::GRAPPLING);
    target.breakOutOfGrapple();

    EXPECT_FALSE(target.isAffectedBy(Conditions::GRAPPLED));
    EXPECT_FALSE(grappler.isAffectedBy(Conditions::GRAPPLING));
  }

  TEST(GrappleTest, GrappleEndsWhenGrapplerIncapacitated)
  {
    BugbearWarrior grappler("Grappler");
    Goblin target(1);
    OnHitGrapple(12).hit(&grappler, nullptr, &target, 1.0, 0.0);
    ASSERT_TRUE(target.isAffectedBy(Conditions::GRAPPLED));

    grappler.applyCondition(Condition(Conditions::INCAPACITATED, &grappler));
    target.endGrappleIfGrapplerIncapacitated();

    EXPECT_FALSE(target.isAffectedBy(Conditions::GRAPPLED));
    EXPECT_FALSE(grappler.isAffectedBy(Conditions::GRAPPLING));
  }

  TEST(GrappleTest, GrappledCreatureNeedsToBreakOutOnItsAction)
  {
    BugbearWarrior grappler("Grappler");
    Goblin target(1);
    OnHitGrapple(12).hit(&grappler, nullptr, &target, 1.0, 0.0);

    auto grappleCondition = target.needsToBreakOutOfGrapple();
    ASSERT_TRUE(grappleCondition.has_value());
    EXPECT_EQ(grappleCondition->dc, 12);
    EXPECT_EQ(grappleCondition->initiator, &grappler);
  }
}
