#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/geometry.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "spells/spell_stats.hpp"
#include "combatants/goblin.hpp"
#include "combatants/sorcerer_lvl_1.hpp"
#include "combatants/bugbear_warrior.hpp"
#include "combatants/stone_giant.hpp"
#include "combatants/wild_heart_barbarian_lvl_3.hpp"
#include "combatants/battlemaster_fighter_lvl_5.hpp"
#include "combatants/giant_toad.hpp"
#include "combatants/green_dragon_wyrmling.hpp"
#include "combatants/ogre.hpp"
#include <set>
#include <algorithm>
#include <memory>
#include <chrono>

using namespace enc;

namespace {

class AbilityTest : public ::testing::Test {
protected:

  BattleMap *battleMap;
  Teams *teams;
  Session *session;
  Goblin* goblin;
//   Bugbear* bugbear;
  SorcererLvl1* sorcerer_lvl_1;
//   WildHeartBarbarianLvl3* wild_heart_barbarian;
//   BattlemasterFighterLvl5* battlemaster_fighter_lvl_5;
//   StoneGiant* stone_giant;
//   Ogre* ogre;
//   GiantToad* giant_toad;
//   GreenDragonWyrmling* green_dragon_wyrmling;

  void SetUp() override
  {
    BattleMap::resetInstance(); // Reset the singleton instance before each test
    battleMap = &BattleMap::getInstance();
    Teams::resetInstance();
    teams = &Teams::getInstance();
    session = new Session();
    goblin = new Goblin(1);
    sorcerer_lvl_1 = new SorcererLvl1(1);
    // bugbear = new Bugbear(1);
    // wild_heart_barbarian = new WildHeartBarbarianLvl3(1);
    // stone_giant = new StoneGiant(1);
    // battlemaster_fighter_lvl_5 = new BattlemasterFighterLvl5(1);
    // ogre = new Ogre(1);
    // giant_toad = new GiantToad(1);
    // green_dragon_wyrmling = new GreenDragonWyrmling(1);
  }

};

TEST_F(AbilityTest, FireboltCalculateThreatToTargetDelta) {
  battleMap->setCombatantCoordinates(*goblin, Coord({5, 0}));
  battleMap->setCombatantCoordinates(*sorcerer_lvl_1, Coord({0, 0}));
  teams->addCombatantToTeam(*goblin, Color::RED);
  teams->addCombatantToTeam(*sorcerer_lvl_1, Color::BLUE);

  std::shared_ptr<ActoidFactory> actoidFactory = sorcerer_lvl_1->getActionFactory(AbilityType::FIREBOLT).lock();
  std::shared_ptr<FireboltFactory> fireboltFactory = std::dynamic_pointer_cast<FireboltFactory>(actoidFactory);

  ASSERT_NE(fireboltFactory, nullptr) << "Failed to cast ActoidFactory to FireboltFactory";

  ThreatModifiers modifiers;

  // Test with advantage
  modifiers.set(ThreatModifierType::ROLL_TYPE, RollType::ADVANTAGE);
  double advantageThreat = fireboltFactory->calculateThreatToTargetDelta(goblin, modifiers);
  EXPECT_GT(advantageThreat, 0);

  // Test with disadvantage
  modifiers.set(ThreatModifierType::ROLL_TYPE, RollType::DISADVANTAGE);
  double disadvantageThreat = fireboltFactory->calculateThreatToTargetDelta(goblin, modifiers);
  EXPECT_LT(disadvantageThreat, 0);

  // Test with flat bonus to hit
  modifiers.clear();
  modifiers.set(ThreatModifierType::TO_HIT_FLAT, 2);
  double bonusToHitThreat = fireboltFactory->calculateThreatToTargetDelta(goblin, modifiers);
  EXPECT_GT(bonusToHitThreat, 0);

  // Test with a negative flat bonus to hit
  modifiers.set(ThreatModifierType::TO_HIT_FLAT, -2);
  double negativeBonusToHitThreat = fireboltFactory->calculateThreatToTargetDelta(goblin, modifiers);
  EXPECT_LT(negativeBonusToHitThreat, 0);

  // Test with increased AC
  modifiers.clear();
  modifiers.set(ThreatModifierType::TARGET_AC, 2);
  double increasedACThreat = fireboltFactory->calculateThreatToTargetDelta(goblin, modifiers);
  EXPECT_LT(increasedACThreat, 0);

  // Test with multiple modifiers
  modifiers.clear();
  modifiers.set(ThreatModifierType::TO_HIT_FLAT, 2);
  modifiers.set(ThreatModifierType::TARGET_AC, 1);
  double multiModifierThreatOne = fireboltFactory->calculateThreatToTargetDelta(goblin, modifiers);
  // The combined effect should be positive (advantage and +2 to hit outweigh +1 AC)
  EXPECT_GT(multiModifierThreatOne, 0);

  // Test a combination of multiple positive effects plus a negative with and overall positive effect
  modifiers.set(ThreatModifierType::ROLL_TYPE, RollType::ADVANTAGE);
  double multiModifierThreatTwo = fireboltFactory->calculateThreatToTargetDelta(goblin, modifiers);
  EXPECT_GT(multiModifierThreatTwo, multiModifierThreatOne);
}

}
