#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/action_resolver.hpp"
#include "actions/attack.hpp"
#include "actions/melee_attack.hpp"
#include "actions/action_types.hpp"
#include "abilities/on_hit_mastery.hpp"
#include "abilities/weapon_mastery_effects.hpp"
#include "effects/effect_tracker.hpp"
#include "combatants/goblin.hpp"
#include "combatants/wild_heart_barbarian_lvl_3.hpp"
#include <algorithm>
#include <memory>
#include <vector>

using namespace enc;

namespace
{
  /**
   * Tests for the 2024 weapon-mastery layer: how masteries are attached to a weapon (Graze on-miss damage,
   * the OnHitMastery rider), the once-per-turn Cleave bookkeeping, the Slow speed reduction, and the way the
   * Sap/Vex riders feed Disadvantage/Advantage into the attack-roll logic via collectAttackRollTypes.
   */
  class WeaponMasteryTest : public ::testing::Test
  {
  protected:
    BattleMap *battleMap;
    Teams *teams;
    Session *session;
    Goblin *attacker;
    Goblin *target;

    void SetUp() override
    {
      BattleMap::resetInstance();
      battleMap = &BattleMap::getInstance();
      Teams::resetInstance();
      teams = &Teams::getInstance();
      EffectTracker::resetInstance();
      session = new Session();
      attacker = new Goblin("AttackerGoblin");
      target = new Goblin("TargetGoblin");

      teams->addCombatantToTeam(*attacker, Color::BLUE);
      teams->addCombatantToTeam(*target, Color::RED);
      battleMap->buildBaseAdjacencyMatrix();
      battleMap->setCombatantCoordinates(*attacker, Coord{2, 2});
      battleMap->setCombatantCoordinates(*target, Coord{3, 2});
    }

    void TearDown() override { EffectTracker::getInstance().clearEffects(); }

    static std::shared_ptr<Attack> makeMeleeAttack(Combatant *atk, Combatant *tgt)
    {
      auto factory = atk->getActionFactory(AbilityType::MELEE_ATTACK).lock();
      return std::dynamic_pointer_cast<Attack>(factory->create(static_cast<void *>(tgt)));
    }
  };

  // The Wild Heart Barbarian's greataxe carries Cleave and its javelin carries Slow.
  TEST_F(WeaponMasteryTest, BarbarianWeaponsCarryExpectedMasteries)
  {
    WildHeartBarbarianLvl3 barbarian(1);

    bool sawCleave = false;
    bool sawSlow = false;
    for(const auto &factory : barbarian.getActionFactoriesConst())
      {
        if(auto *attackFactory = dynamic_cast<AttackFactory *>(factory.get()))
          {
            if(attackFactory->getMastery() == WeaponMastery::CLEAVE)
              {
                sawCleave = true;
              }
            if(attackFactory->getMastery() == WeaponMastery::SLOW)
              {
                sawSlow = true;
              }
          }
      }
    EXPECT_TRUE(sawCleave) << "Greataxe should have the Cleave mastery";
    EXPECT_TRUE(sawSlow) << "Javelin should have the Slow mastery";
  }

  // Graze is stored as on-miss damage equal to the weapon's ability modifier; the mastery itself is recorded
  // but no OnHit rider is attached for it.
  TEST_F(WeaponMasteryTest, ApplyGrazeStoresOnMissDamage)
  {
    auto factory = attacker->addMeleeAttack("Graze weapon", attacker, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Slashing, 1);
    attacker->applyWeaponMastery(factory, WeaponMastery::GRAZE);

    auto *attackFactory = dynamic_cast<AttackFactory *>(factory.get());
    ASSERT_NE(attackFactory, nullptr);
    EXPECT_EQ(attackFactory->getMastery(), WeaponMastery::GRAZE);
    EXPECT_EQ(attackFactory->getGrazeDamage(), attackFactory->getDmgBonus());
    EXPECT_TRUE(attackFactory->getOnHits().empty());
  }

  // The on-hit masteries (e.g. Vex) bolt an OnHitMastery rider onto the weapon; Nick and None do not.
  TEST_F(WeaponMasteryTest, OnHitMasteryAttachesRider)
  {
    auto vexWeapon = attacker->addMeleeAttack("Vex weapon", attacker, 5, std::vector<Die>{{1, 6}}, 3, DamageType::Slashing, 1);
    attacker->applyWeaponMastery(vexWeapon, WeaponMastery::VEX);
    auto *vexFactory = dynamic_cast<AttackFactory *>(vexWeapon.get());
    ASSERT_NE(vexFactory, nullptr);
    EXPECT_EQ(vexFactory->getMastery(), WeaponMastery::VEX);
    EXPECT_EQ(vexFactory->getOnHits().size(), 1u);

    auto nickWeapon = attacker->addMeleeAttack("Nick weapon", attacker, 5, std::vector<Die>{{1, 6}}, 3, DamageType::Slashing, 1);
    attacker->applyWeaponMastery(nickWeapon, WeaponMastery::NICK);
    auto *nickFactory = dynamic_cast<AttackFactory *>(nickWeapon.get());
    ASSERT_NE(nickFactory, nullptr);
    EXPECT_EQ(nickFactory->getMastery(), WeaponMastery::NICK);
    EXPECT_TRUE(nickFactory->getOnHits().empty());
  }

  // Cleave can be claimed only once per turn; the claim resets at the start of a new turn.
  TEST_F(WeaponMasteryTest, CleaveIsOncePerTurn)
  {
    EXPECT_TRUE(attacker->tryUseMasteryThisTurn(WeaponMastery::CLEAVE));
    EXPECT_FALSE(attacker->tryUseMasteryThisTurn(WeaponMastery::CLEAVE));

    attacker->newTurn();
    EXPECT_TRUE(attacker->tryUseMasteryThisTurn(WeaponMastery::CLEAVE));
  }

  // Slow drops the target's Speed by 10 ft (2 cells) on activation and restores it on deactivation.
  TEST_F(WeaponMasteryTest, SlowedEffectReducesAndRestoresSpeed)
  {
    const int originalSpeed = target->getSpeed();

    auto slowed = std::make_shared<SlowedEffect>(attacker, target);
    slowed->activate();
    EXPECT_EQ(target->getSpeed(), originalSpeed - 2);

    slowed->deactivate();
    EXPECT_EQ(target->getSpeed(), originalSpeed);
  }

  // Hitting with a Sap weapon Sapps the target, which gives it Disadvantage on its next attack roll.
  TEST_F(WeaponMasteryTest, SapHitGivesTargetDisadvantage)
  {
    auto &effectTracker = EffectTracker::getInstance();
    auto attack = makeMeleeAttack(attacker, target);
    ASSERT_NE(attack, nullptr);

    OnHitMastery sap(WeaponMastery::SAP);
    sap.hit(attacker, attack.get(), target, /*multiplier=*/1.0, /*dmgSoFar=*/0.0);
    EXPECT_TRUE(effectTracker.isAffectingCombatant(target, EffectType::SAPPED));

    // The sapped target now attacks the goblin with Disadvantage.
    ActionResolver resolver;
    auto retaliation = makeMeleeAttack(target, attacker);
    ASSERT_NE(retaliation, nullptr);
    auto types = resolver.collectAttackRollTypes(retaliation.get(), attacker, target);
    EXPECT_EQ(types.count(RollType::DISADVANTAGE), 1u);
  }

  // Hitting with a Vex weapon gives the wielder Advantage on its next attack roll against that target.
  TEST_F(WeaponMasteryTest, VexHitGivesWielderAdvantage)
  {
    auto attack = makeMeleeAttack(attacker, target);
    ASSERT_NE(attack, nullptr);

    OnHitMastery vex(WeaponMastery::VEX);
    vex.hit(attacker, attack.get(), target, /*multiplier=*/1.0, /*dmgSoFar=*/0.0);

    ActionResolver resolver;
    auto followUp = makeMeleeAttack(attacker, target);
    ASSERT_NE(followUp, nullptr);
    auto types = resolver.collectAttackRollTypes(followUp.get(), target, attacker);
    EXPECT_EQ(types.count(RollType::ADVANTAGE), 1u);
  }
} // namespace
