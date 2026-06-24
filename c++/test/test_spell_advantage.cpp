#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/misc.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/action_resolver.hpp"
#include "actions/attack.hpp"
#include "actions/melee_attack.hpp"
#include "actions/action_types.hpp"
#include "spells/faerie_fire.hpp"
#include "spells/moonbeam.hpp"
#include "effects/effect_tracker.hpp"
#include "effects/effect.hpp"
#include "combatants/goblin.hpp"
#include "combatants/moon_druid_lvl_3.hpp"
#include <memory>

using namespace enc;

namespace
{
  /**
   * Tests for the two spells whose attack-roll / area interaction was recently added: Faerie Fire (attacks
   * against an outlined target have Advantage) and Moonbeam (a 2nd-level Radiant cylinder).
   */
  class SpellAdvantageTest : public ::testing::Test
  {
  protected:
    BattleMap *battleMap;
    Teams *teams;
    Session *session;

    void SetUp() override
    {
      BattleMap::resetInstance();
      battleMap = &BattleMap::getInstance();
      Teams::resetInstance();
      teams = &Teams::getInstance();
      EffectTracker::resetInstance();
      session = new Session();
    }

    void TearDown() override { EffectTracker::getInstance().clearEffects(); }

    static std::shared_ptr<Attack> makeMeleeAttack(Combatant *atk, Combatant *tgt)
    {
      auto factory = atk->getActionFactory(AbilityType::MELEE_ATTACK).lock();
      return std::dynamic_pointer_cast<Attack>(factory->create(static_cast<void *>(tgt)));
    }
  };

  // A creature outlined by Faerie Fire grants Advantage to anyone attacking it.
  TEST_F(SpellAdvantageTest, FaerieFireGivesAttackersAdvantage)
  {
    MoonDruidLvl3 druid(1);
    Goblin attacker("AttackerGoblin");
    Goblin target("TargetGoblin");

    teams->addCombatantToTeam(druid, Color::BLUE);
    teams->addCombatantToTeam(attacker, Color::BLUE);
    teams->addCombatantToTeam(target, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(druid, Coord{2, 5});
    battleMap->setCombatantCoordinates(target, Coord{5, 5});
    battleMap->setCombatantCoordinates(attacker, Coord{4, 5});

    // Force the target to fail its Dexterity save so it is reliably outlined.
    target.setSavingThrow(SavingThrow::DEX, -100);

    auto factory = std::dynamic_pointer_cast<FaerieFireFactory>(druid.getActionFactory(AbilityType::FAERIE_FIRE).lock());
    ASSERT_NE(factory, nullptr);

    Coord coord = battleMap->getCombatantCoordinates(target).getRoot();
    auto faerieFire = std::dynamic_pointer_cast<FaerieFire>(factory->create(static_cast<void *>(&coord)));
    ASSERT_NE(faerieFire, nullptr);
    EffectTracker::getInstance().add(std::dynamic_pointer_cast<Effect>(faerieFire));
    // rollSavingThrow auto-succeeds on a natural 20 regardless of the modifier, so a single activation
    // can flakily leave the target un-outlined. Retry until it fails its save (overwhelmingly likely).
    for(int i = 0; i < 100 && !faerieFire->isAffecting(&target); ++i)
      {
        faerieFire->activate();
      }

    ASSERT_TRUE(EffectTracker::getInstance().isAffectingCombatant(&target, EffectType::FAERIE_FIRE));

    ActionResolver resolver;
    auto attack = makeMeleeAttack(&attacker, &target);
    ASSERT_NE(attack, nullptr);
    auto types = resolver.collectAttackRollTypes(attack.get(), &target, &attacker);
    EXPECT_EQ(types.count(RollType::ADVANTAGE), 1u);
  }

  // Without Faerie Fire (or any other source) the same attack is a straight roll.
  TEST_F(SpellAdvantageTest, NoAdvantageWithoutFaerieFire)
  {
    Goblin attacker("AttackerGoblin");
    Goblin target("TargetGoblin");
    teams->addCombatantToTeam(attacker, Color::BLUE);
    teams->addCombatantToTeam(target, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(attacker, Coord{4, 5});
    battleMap->setCombatantCoordinates(target, Coord{5, 5});

    ActionResolver resolver;
    auto attack = makeMeleeAttack(&attacker, &target);
    ASSERT_NE(attack, nullptr);
    auto types = resolver.collectAttackRollTypes(attack.get(), &target, &attacker);
    EXPECT_EQ(types.count(RollType::ADVANTAGE), 0u);
  }

  // Moonbeam is a 2nd-level, 120 ft, Radiant spell whose area effect reports EffectType::MOONBEAM.
  TEST_F(SpellAdvantageTest, MoonbeamConfiguration)
  {
    MoonDruidLvl3 druid(1);
    teams->addCombatantToTeam(druid, Color::BLUE);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(druid, Coord{2, 5});

    auto raw = druid.addMoonbeam(13);
    auto factory = std::dynamic_pointer_cast<MoonbeamFactory>(raw);
    ASSERT_NE(factory, nullptr);

    EXPECT_EQ(MoonbeamFactory::level, 2);
    EXPECT_EQ(MoonbeamFactory::range, SpellRange::FEET_120);
    EXPECT_EQ(MoonbeamFactory::dmgType, DamageType::Radiant);

    Coord coord{5, 5};
    auto moonbeam = std::dynamic_pointer_cast<Moonbeam>(factory->create(static_cast<void *>(&coord)));
    ASSERT_NE(moonbeam, nullptr);
    EXPECT_EQ(moonbeam->getEffectType(), EffectType::MOONBEAM);
  }
} // namespace
