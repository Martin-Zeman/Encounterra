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

class CombatantTest : public ::testing::Test {
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
  Ogre *ogre;
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
    ogre = new Ogre(1);
    // giant_toad = new GiantToad(1);
    // green_dragon_wyrmling = new GreenDragonWyrmling(1);
  }

};

TEST_F(CombatantTest, ReceiveDmgBasic) {
    // Basic damage reception
    int initialHp = goblin->getCurrentHp();
    int dmg = goblin->receiveDmg(5, DamageType::Slashing);
    EXPECT_EQ(dmg, 5);
    EXPECT_EQ(goblin->getCurrentHp(), initialHp - 5);
}

TEST_F(CombatantTest, ReceiveDmgResistance) {
    // Test with resistance to slashing
    goblin->addResistance(DamageType::Slashing);
    int initialHp = goblin->getCurrentHp();
    int dmg = goblin->receiveDmg(9, DamageType::Slashing);
    EXPECT_EQ(dmg, 4);  // Half damage due to resistance (rounded down)
    EXPECT_EQ(goblin->getCurrentHp(), initialHp - 4);
}

TEST_F(CombatantTest, ReceiveDmgImmunity) {
    // Test with immunity to fire
    goblin->addImmunity(DamageType::Fire);
    int initialHp = goblin->getCurrentHp();
    int dmg = goblin->receiveDmg(10, DamageType::Fire);
    EXPECT_EQ(dmg, 0);  // No damage due to immunity
    EXPECT_EQ(goblin->getCurrentHp(), initialHp);
}

TEST_F(CombatantTest, ReceiveDmgVulnerability) {
    // Test with vulnerability to fire
    ogre->addVulnerability(DamageType::Fire);
    int initialHp = ogre->getCurrentHp();
    
    int dmg = ogre->receiveDmg(10, DamageType::Fire);
    EXPECT_EQ(dmg, 20);  // Double damage due to vulnerability
    EXPECT_EQ(ogre->getCurrentHp(), initialHp - 20);
}

TEST_F(CombatantTest, ReceiveCompoundDmg) {
    std::vector<std::pair<int, DamageType>> damages = {
        {5, DamageType::Slashing},
        {3, DamageType::Fire},
        {2, DamageType::Poison}
    };
    
    int initialHp = ogre->getCurrentHp();
    int totalDmg = ogre->receiveCompoundDmg(damages);
    EXPECT_EQ(totalDmg, 10);
    EXPECT_EQ(ogre->getCurrentHp(), initialHp - 10);
}

TEST_F(CombatantTest, ReceiveCompoundDmgMixed) {
    // Create goblin with mixed resistances/vulnerabilities
    ogre->addResistance(DamageType::Slashing);
    ogre->addVulnerability(DamageType::Fire);
    ogre->addImmunity(DamageType::Poison);
    
    std::vector<std::pair<int, DamageType>> damages = {
        {10, DamageType::Slashing},  // Should be 5 due to resistance
        {5, DamageType::Fire},       // Should be 10 due to vulnerability
        {8, DamageType::Poison}      // Should be 0 due to immunity
    };
    
    int initialHp = ogre->getCurrentHp();
    int totalDmg = ogre->receiveCompoundDmg(damages);
    EXPECT_EQ(totalDmg, 15);  // 5 + 10 + 0
    EXPECT_EQ(ogre->getCurrentHp(), initialHp - 15);
}

TEST_F(CombatantTest, UndeadFortitudeSave) {
    goblin->addUndeadFortitude();
    goblin->setSavingThrow(SavingThrow::CON, 20); // Making it a guaranteed success save for a nat 1
    // Should survive due to Undead Fortitude (assuming saving throw succeeds)
    int dmg = goblin->receiveDmg(10, DamageType::Slashing);
    
    EXPECT_EQ(goblin->getCurrentHp(), 1);
}

TEST_F(CombatantTest, UndeadFortitudeRadiantDmg) {
    goblin->addUndeadFortitude();
    goblin->setSavingThrow(SavingThrow::CON, 20); // Making it a guaranteed success save for a nat 1
    int dmg = goblin->receiveDmg(10, DamageType::Radiant);
    
    EXPECT_EQ(goblin->getCurrentHp(), -3);
}

TEST_F(CombatantTest, TemporaryHpDamage) {
    goblin->setTemporaryHp(5);
    int initialHp = goblin->getCurrentHp();
    
    // Damage less than temp HP
    int dmg1 = goblin->receiveDmg(3, DamageType::Slashing);
    EXPECT_EQ(dmg1, 3);
    EXPECT_EQ(goblin->getTemporaryHp(), 2);
    EXPECT_EQ(goblin->getCurrentHp(), initialHp);
    
    // Damage more than remaining temp HP
    int dmg2 = goblin->receiveDmg(5, DamageType::Slashing);
    EXPECT_EQ(dmg2, 5);
    EXPECT_EQ(goblin->getTemporaryHp(), 0);
    EXPECT_EQ(goblin->getCurrentHp(), initialHp - 3);  // 5 - 2 temp HP = 3 real damage
}

}
