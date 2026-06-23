#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/interfaces.hpp"
#include "core/types.hpp"
#include "core/resources.hpp"
#include "combatants/moon_druid_lvl_3.hpp"
#include "combatants/goblin.hpp"
#include "combatants/bugbear_warrior.hpp"
#include "combatants/tiger.hpp"
#include "combatants/lion.hpp"
#include "combatants/dire_wolf.hpp"
#include "combatants/giant_spider.hpp"
#include "abilities/wildshape.hpp"
#include "abilities/wildshape_utils.hpp"
#include "abilities/pounce.hpp"
#include "abilities/roar.hpp"
#include "abilities/on_hit_prone.hpp"
#include "spells/flaming_sphere.hpp"
#include "spells/faerie_fire.hpp"
#include "spells/spike_growth.hpp"
#include "effects/effect_tracker.hpp"
#include "actions/action_types.hpp"
#include <algorithm>
#include <deque>
#include <memory>

using namespace enc;

namespace
{

  class MoonDruidLvl3Test : public ::testing::Test
  {
  protected:
    BattleMap *battleMap;
    Teams *teams;
    Session *session;
    MoonDruidLvl3 *druid;
    Goblin *goblin;

    void SetUp() override
    {
      BattleMap::resetInstance();
      battleMap = &BattleMap::getInstance();
      Teams::resetInstance();
      teams = &Teams::getInstance();
      EffectTracker::resetInstance();
      session = new Session();
      druid = new MoonDruidLvl3(1);
      goblin = new Goblin(1);
    }

    void TearDown() override
    {
      EffectTracker::getInstance().clearEffects();
    }

    static bool hasFactory(const std::vector<std::shared_ptr<ActoidFactory>> &factories, AbilityType type)
    {
      return std::any_of(factories.begin(), factories.end(),
                         [type](const std::shared_ptr<ActoidFactory> &f) { return f->getAbilityType() == type; });
    }

    static bool hasNamedFactory(const std::vector<std::shared_ptr<ActoidFactory>> &factories, const std::string &abilityName)
    {
      return std::any_of(factories.begin(), factories.end(),
                         [&abilityName](const std::shared_ptr<ActoidFactory> &f) { return f->_abilityName == abilityName; });
    }

    static ActoidFactory *findFactory(const std::vector<std::shared_ptr<ActoidFactory>> &factories, AbilityType type)
    {
      for(const auto &f : factories)
        if(f->getAbilityType() == type)
          return f.get();
      return nullptr;
    }

    // Populate and return the druid's preallocated Wild Shape forms (normally done by RoundManager::prepCombatants).
    void prepWildshapeForms()
    {
      for(const auto &factory : druid->getBonusActionFactoriesConst())
        {
          if(factory->getAbilityType() == AbilityType::MOON_WILDSHAPE)
            {
              auto *wf = static_cast<WildshapeFactory *>(factory.get());
              druid->setAvailableWildshapeForms(preallocateWildshapeForms(druid, AbilityType::MOON_WILDSHAPE, *wf));
              return;
            }
        }
    }

    std::shared_ptr<Wildshape> findForm(int classId)
    {
      for(const auto &w : druid->getAvailableWildshapeForms())
        if(w->getForm()->getClassId() == classId)
          return w;
      return nullptr;
    }

    // True if the action plan contains at least one actoid of the given concrete type.
    template <typename ActoidT>
    static bool planContains(const std::deque<std::shared_ptr<Actoid>> &plan)
    {
      return std::any_of(plan.begin(), plan.end(),
                         [](const std::shared_ptr<Actoid> &a) { return std::dynamic_pointer_cast<ActoidT>(a) != nullptr; });
    }

    std::deque<std::shared_ptr<Actoid>> planFor(Combatant *combatant)
    {
      auto [distances, shortestPaths] = battleMap->calcDijkstra(*combatant);
      combatant->setShortestPathsCache(shortestPaths);
      return combatant->calculateActionPlan(distances, shortestPaths);
    }
  };

  // ---------------------------------------------------------------------------
  // Base stats, saving throws, skills.
  // ---------------------------------------------------------------------------

  TEST_F(MoonDruidLvl3Test, BaseStats)
  {
    EXPECT_EQ(druid->getMaxHp(), 27);
    EXPECT_EQ(druid->getAC(), 13);
    EXPECT_EQ(druid->getDC(), 13);
    EXPECT_EQ(druid->getLevel(), 3);
    EXPECT_EQ(druid->getSpeed(), 7); // 35 ft stored as 7 grid cells (5 ft each)
  }

  TEST_F(MoonDruidLvl3Test, SavingThrows)
  {
    EXPECT_EQ(druid->getSavingThrow(SavingThrow::STR), 0);
    EXPECT_EQ(druid->getSavingThrow(SavingThrow::DEX), 1);
    EXPECT_EQ(druid->getSavingThrow(SavingThrow::CON), 3);
    EXPECT_EQ(druid->getSavingThrow(SavingThrow::INT), 4);
    EXPECT_EQ(druid->getSavingThrow(SavingThrow::WIS), 5);
    EXPECT_EQ(druid->getSavingThrow(SavingThrow::CHA), 1);
  }

  // ---------------------------------------------------------------------------
  // Loadout: weapons, spells, class feature.
  // ---------------------------------------------------------------------------

  TEST_F(MoonDruidLvl3Test, WeaponFactoriesPresent)
  {
    const auto &actions = druid->getActionFactoriesConst();
    EXPECT_TRUE(hasNamedFactory(actions, "Scimitar")); // melee
    EXPECT_TRUE(hasNamedFactory(actions, "Longbow"));  // ranged
    EXPECT_TRUE(hasFactory(actions, AbilityType::MELEE_ATTACK));
    EXPECT_TRUE(hasFactory(actions, AbilityType::RANGED_ATTACK));
    // Scimitar is also the reaction (opportunity) attack (registered as a melee attack factory).
    EXPECT_TRUE(hasNamedFactory(druid->getReactionFactoriesConst(), "Scimitar"));
  }

  TEST_F(MoonDruidLvl3Test, SpellFactoriesPresent)
  {
    const auto &actions = druid->getActionFactoriesConst();
    EXPECT_TRUE(hasFactory(actions, AbilityType::FLAMING_SPHERE));
    EXPECT_TRUE(hasFactory(actions, AbilityType::HOLD_PERSON));
    EXPECT_TRUE(hasFactory(actions, AbilityType::FAERIE_FIRE));
    EXPECT_TRUE(hasFactory(actions, AbilityType::SPIKE_GROWTH));
    EXPECT_TRUE(hasFactory(actions, AbilityType::THUNDERWAVE));
    // Healing Word is a bonus action.
    EXPECT_TRUE(hasFactory(druid->getBonusActionFactoriesConst(), AbilityType::HEALING_WORD));
  }

  TEST_F(MoonDruidLvl3Test, MoonWildshapePresent)
  {
    EXPECT_TRUE(hasFactory(druid->getBonusActionFactoriesConst(), AbilityType::MOON_WILDSHAPE));
  }

  // Every leveled-spell factory must be flagged TRANSITIONS_TO_WILDSHAPE so it survives the shape stash.
  TEST_F(MoonDruidLvl3Test, LeveledSpellsFlaggedCastableWhileShaped)
  {
    for(AbilityType type : {AbilityType::FLAMING_SPHERE, AbilityType::HOLD_PERSON, AbilityType::FAERIE_FIRE,
                            AbilityType::SPIKE_GROWTH, AbilityType::THUNDERWAVE})
      {
        auto *f = findFactory(druid->getActionFactoriesConst(), type);
        ASSERT_NE(f, nullptr);
        EXPECT_TRUE(f->hasFlag(FactoryFlags::TRANSITIONS_TO_WILDSHAPE));
      }
    auto *healingWord = findFactory(druid->getBonusActionFactoriesConst(), AbilityType::HEALING_WORD);
    ASSERT_NE(healingWord, nullptr);
    EXPECT_TRUE(healingWord->hasFlag(FactoryFlags::TRANSITIONS_TO_WILDSHAPE));
  }

  // The weapon attacks are NOT castable while shaped (they get stashed during Wild Shape).
  TEST_F(MoonDruidLvl3Test, WeaponsNotFlaggedCastableWhileShaped)
  {
    for(const auto &f : druid->getActionFactoriesConst())
      {
        if(f->_abilityName == "Scimitar" || f->_abilityName == "Longbow")
          EXPECT_FALSE(f->hasFlag(FactoryFlags::TRANSITIONS_TO_WILDSHAPE));
      }
  }

  // ---------------------------------------------------------------------------
  // Wild Shape forms (Circle of the Moon, level 3).
  // ---------------------------------------------------------------------------

  TEST_F(MoonDruidLvl3Test, AvailableFormsIncludeExpectedBeasts)
  {
    prepWildshapeForms();
    EXPECT_NE(findForm(Tiger::getStaticClassId()), nullptr);
    EXPECT_NE(findForm(Lion::getStaticClassId()), nullptr);
    EXPECT_NE(findForm(DireWolf::getStaticClassId()), nullptr);
    EXPECT_NE(findForm(GiantSpider::getStaticClassId()), nullptr);
  }

  // ---------------------------------------------------------------------------
  // Wild Shape mechanics (2024): temp HP, AC floor, speed, factory swap.
  // ---------------------------------------------------------------------------

  TEST_F(MoonDruidLvl3Test, ShapingGrantsThreeTimesLevelTempHp)
  {
    prepWildshapeForms();
    auto tiger = findForm(Tiger::getStaticClassId());
    ASSERT_NE(tiger, nullptr);
    EXPECT_EQ(druid->getTemporaryHp(), 0);

    tiger->activate();
    // Circle of the Moon grants 3 x level temporary hit points.
    EXPECT_EQ(druid->getTemporaryHp(), 3 * druid->getLevel());
  }

  TEST_F(MoonDruidLvl3Test, ShapingRaisesAcToMoonFloor)
  {
    prepWildshapeForms();
    auto tiger = findForm(Tiger::getStaticClassId()); // beast AC 13
    ASSERT_NE(tiger, nullptr);

    tiger->activate();
    // AC = max(beast AC 13, 13 + WisMod 3) = 16.
    EXPECT_EQ(druid->getAC(), 16);
  }

  TEST_F(MoonDruidLvl3Test, ShapingAdoptsBeastSpeed)
  {
    prepWildshapeForms();
    auto tiger = findForm(Tiger::getStaticClassId()); // 40 ft = 8 cells
    ASSERT_NE(tiger, nullptr);

    tiger->activate();
    EXPECT_EQ(druid->getSpeed(), 8);
  }

  TEST_F(MoonDruidLvl3Test, ShapingAdoptsBeastSize)
  {
    prepWildshapeForms();
    auto tiger = findForm(Tiger::getStaticClassId()); // Large beast
    ASSERT_NE(tiger, nullptr);
    ASSERT_EQ(druid->getSize(), Size::MEDIUM);

    tiger->activate();
    EXPECT_EQ(druid->getSize(), Size::LARGE);

    tiger->deactivate();
    EXPECT_EQ(druid->getSize(), Size::MEDIUM);
  }

  TEST_F(MoonDruidLvl3Test, ShapingStashesWeaponsAndGraftsBeastAttacks)
  {
    prepWildshapeForms();
    auto tiger = findForm(Tiger::getStaticClassId());
    ASSERT_NE(tiger, nullptr);

    tiger->activate();
    const auto &actions = druid->getActionFactoriesConst();
    // Druid weapons are suppressed while shaped.
    EXPECT_FALSE(hasNamedFactory(actions, "Scimitar"));
    EXPECT_FALSE(hasNamedFactory(actions, "Longbow"));
    // The beast's signature attack is grafted on.
    EXPECT_TRUE(hasNamedFactory(actions, "Pounce"));
  }

  TEST_F(MoonDruidLvl3Test, ShapingKeepsFlaggedSpellsAvailable)
  {
    prepWildshapeForms();
    auto tiger = findForm(Tiger::getStaticClassId());
    ASSERT_NE(tiger, nullptr);

    tiger->activate();
    const auto &actions = druid->getActionFactoriesConst();
    // Circle of the Moon spell loadout survives the shape.
    EXPECT_TRUE(hasFactory(actions, AbilityType::FLAMING_SPHERE));
    EXPECT_TRUE(hasFactory(actions, AbilityType::FAERIE_FIRE));
    EXPECT_TRUE(hasFactory(actions, AbilityType::SPIKE_GROWTH));
    EXPECT_TRUE(hasFactory(actions, AbilityType::THUNDERWAVE));
    EXPECT_TRUE(hasFactory(actions, AbilityType::HOLD_PERSON));
    EXPECT_TRUE(hasFactory(druid->getBonusActionFactoriesConst(), AbilityType::HEALING_WORD));
  }

  TEST_F(MoonDruidLvl3Test, ShapingRecordsActiveFormId)
  {
    prepWildshapeForms();
    auto tiger = findForm(Tiger::getStaticClassId());
    ASSERT_NE(tiger, nullptr);
    EXPECT_EQ(druid->getActiveWildshapeFormId(), 0);

    tiger->activate();
    EXPECT_EQ(druid->getActiveWildshapeFormId(), Tiger::getStaticClassId());
  }

  // Same-form restriction: the active form is excluded from the next reshape options.
  TEST_F(MoonDruidLvl3Test, CannotReshapeIntoActiveForm)
  {
    prepWildshapeForms();
    auto tiger = findForm(Tiger::getStaticClassId());
    ASSERT_NE(tiger, nullptr);
    tiger->activate();

    auto *factory = static_cast<WildshapeFactory *>(findFactory(druid->getBonusActionFactoriesConst(), AbilityType::MOON_WILDSHAPE));
    ASSERT_NE(factory, nullptr);
    auto options = factory->createAll();
    for(const auto &opt : options)
      {
        auto ws = std::dynamic_pointer_cast<Wildshape>(opt);
        ASSERT_NE(ws, nullptr);
        EXPECT_NE(ws->getForm()->getClassId(), Tiger::getStaticClassId());
      }
  }

  // ---------------------------------------------------------------------------
  // Damage interaction with Wild Shape temp HP.
  // ---------------------------------------------------------------------------

  TEST_F(MoonDruidLvl3Test, DamageDrainsTempHpFirst)
  {
    prepWildshapeForms();
    auto tiger = findForm(Tiger::getStaticClassId());
    ASSERT_NE(tiger, nullptr);
    tiger->activate(); // 9 temp HP

    druid->receiveDmg(5, DamageType::Slashing);
    EXPECT_EQ(druid->getTemporaryHp(), 4);
    EXPECT_EQ(druid->getCurrentHp(), 27); // real HP untouched
  }

  TEST_F(MoonDruidLvl3Test, DamageOverflowsTempHpIntoRealHp)
  {
    prepWildshapeForms();
    auto tiger = findForm(Tiger::getStaticClassId());
    ASSERT_NE(tiger, nullptr);
    tiger->activate(); // 9 temp HP

    druid->receiveDmg(13, DamageType::Slashing);
    EXPECT_EQ(druid->getTemporaryHp(), 0);
    EXPECT_EQ(druid->getCurrentHp(), 27 - 4); // 13 - 9 carries over
  }

  // The druid is never knocked out of the form: at 0 HP it simply dies.
  TEST_F(MoonDruidLvl3Test, DruidDiesAtZeroHpWhileShaped)
  {
    prepWildshapeForms();
    auto tiger = findForm(Tiger::getStaticClassId());
    ASSERT_NE(tiger, nullptr);
    tiger->activate(); // 9 temp + 27 real = 36 total

    druid->receiveDmg(40, DamageType::Slashing);
    EXPECT_FALSE(druid->isAlive());
    EXPECT_LE(druid->getCurrentHp(), 0);
    // Still recorded as shaped (no automatic revert to a separate beast combatant in 2024 rules).
    EXPECT_EQ(druid->getActiveWildshapeFormId(), Tiger::getStaticClassId());
  }

  // ---------------------------------------------------------------------------
  // Reverting Wild Shape.
  // ---------------------------------------------------------------------------

  TEST_F(MoonDruidLvl3Test, RevertRestoresAcSpeedAndWeapons)
  {
    prepWildshapeForms();
    auto tiger = findForm(Tiger::getStaticClassId());
    ASSERT_NE(tiger, nullptr);
    tiger->activate();
    tiger->deactivate();

    EXPECT_EQ(druid->getAC(), 13);
    EXPECT_EQ(druid->getSpeed(), 7);
    EXPECT_EQ(druid->getActiveWildshapeFormId(), 0);
    const auto &actions = druid->getActionFactoriesConst();
    EXPECT_TRUE(hasNamedFactory(actions, "Scimitar"));
    EXPECT_TRUE(hasNamedFactory(actions, "Longbow"));
    EXPECT_FALSE(hasNamedFactory(actions, "Pounce")); // beast attack removed
  }

  // Temporary hit points granted by Wild Shape persist after reverting (they are NOT cleared on revert).
  TEST_F(MoonDruidLvl3Test, RevertKeepsTempHp)
  {
    prepWildshapeForms();
    auto tiger = findForm(Tiger::getStaticClassId());
    ASSERT_NE(tiger, nullptr);
    tiger->activate(); // 9 temp HP
    tiger->deactivate();

    EXPECT_EQ(druid->getTemporaryHp(), 9);
  }

  // ---------------------------------------------------------------------------
  // Spell behaviour.
  // ---------------------------------------------------------------------------

  TEST_F(MoonDruidLvl3Test, FlamingSphereEnablesAndDisablesRamBonusAction)
  {
    session->addCombatant(druid, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*druid, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{5, 3});

    auto *factory = static_cast<FlamingSphereFactory *>(findFactory(druid->getActionFactoriesConst(), AbilityType::FLAMING_SPHERE));
    ASSERT_NE(factory, nullptr);
    Coord target{3, 3};
    auto sphere = std::dynamic_pointer_cast<FlamingSphere>(factory->create(&target));
    ASSERT_NE(sphere, nullptr);

    // Before casting, the Ram bonus action is not available.
    EXPECT_FALSE(hasFactory(druid->getBonusActionFactoriesConst(), AbilityType::FLAMING_SPHERE_RAM));

    sphere->activate();
    EXPECT_TRUE(hasFactory(druid->getBonusActionFactoriesConst(), AbilityType::FLAMING_SPHERE_RAM));
    // Casting a concentration spell records concentration.
    EXPECT_FALSE(druid->getConcentrationEffect().expired());

    sphere->deactivate();
    EXPECT_FALSE(hasFactory(druid->getBonusActionFactoriesConst(), AbilityType::FLAMING_SPHERE_RAM));
  }

  TEST_F(MoonDruidLvl3Test, FlamingSphereThreatPositive)
  {
    session->addCombatant(druid, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*druid, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{4, 3});

    auto *threat = dynamic_cast<DirectThreatFactory *>(findFactory(druid->getActionFactoriesConst(), AbilityType::FLAMING_SPHERE));
    ASSERT_NE(threat, nullptr);
    EXPECT_GT(threat->calculateThreatToTarget(goblin, {}), 0.0);
  }

  TEST_F(MoonDruidLvl3Test, FaerieFireThreatPositive)
  {
    session->addCombatant(druid, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*druid, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{4, 3});

    auto *threat = dynamic_cast<DirectThreatFactory *>(findFactory(druid->getActionFactoriesConst(), AbilityType::FAERIE_FIRE));
    ASSERT_NE(threat, nullptr);
    EXPECT_GT(threat->calculateThreatToTarget(goblin, {}), 0.0);
  }

  TEST_F(MoonDruidLvl3Test, HoldPersonThreatPositiveForHumanoid)
  {
    auto *bugbear = new BugbearWarrior(1); // humanoid
    session->addCombatant(druid, Color::BLUE);
    session->addCombatant(static_cast<Combatant *>(bugbear), Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*druid, Coord{1, 3});
    battleMap->setCombatantCoordinates(*bugbear, Coord{4, 3});

    auto *threat = dynamic_cast<DirectThreatFactory *>(findFactory(druid->getActionFactoriesConst(), AbilityType::HOLD_PERSON));
    ASSERT_NE(threat, nullptr);
    EXPECT_GT(threat->calculateThreatToTarget(bugbear, {}), 0.0);
  }

  // ---------------------------------------------------------------------------
  // Resource consumption: leveled spells consume a spell slot.
  // ---------------------------------------------------------------------------

  TEST_F(MoonDruidLvl3Test, FlamingSphereUnavailableWhenSlotsDepleted)
  {
    auto *factory = findFactory(druid->getActionFactoriesConst(), AbilityType::FLAMING_SPHERE);
    ASSERT_NE(factory, nullptr);
    auto resource = factory->getResource();
    ASSERT_TRUE(resource.has_value());

    EXPECT_TRUE((*resource)->hasUses(2)); // a 2nd-level slot is available
    druid->getSpellslots().depleteResource(ResourceDepletionLevel::FULLY_DEPLETED);
    EXPECT_FALSE((*resource)->hasUses(2));
  }

  // ---------------------------------------------------------------------------
  // BattleMap::isPathStraight unit tests (mirroring numba is_path_straight,
  // simulator/test/test_abilities.py:1299-1329). Pounce requires a straight
  // approach path, so the geometry helper must match the Python reference.
  // ---------------------------------------------------------------------------

  TEST(PounceGeometryTest, ShortPath)
  {
    CoordVector path{{0, 0}, {1, 1}};
    EXPECT_TRUE(BattleMap::isPathStraight(path, 2));
    EXPECT_FALSE(BattleMap::isPathStraight(path, 1));
  }

  TEST(PounceGeometryTest, SinglePoint)
  {
    CoordVector path{{0, 0}};
    EXPECT_FALSE(BattleMap::isPathStraight(path, 1));
  }

  TEST(PounceGeometryTest, LengthExceedsPath)
  {
    CoordVector path{{0, 0}, {1, 1}, {2, 2}};
    EXPECT_FALSE(BattleMap::isPathStraight(path, 4));
  }

  TEST(PounceGeometryTest, HorizontalPath)
  {
    CoordVector path{{0, 0}, {1, 0}, {2, 0}, {3, 0}};
    EXPECT_TRUE(BattleMap::isPathStraight(path, 4));
  }

  TEST(PounceGeometryTest, VerticalPath)
  {
    CoordVector path{{0, 0}, {0, 1}, {0, 2}, {0, 3}};
    EXPECT_TRUE(BattleMap::isPathStraight(path, 4));
  }

  TEST(PounceGeometryTest, DiagonalPath)
  {
    CoordVector path{{0, 0}, {1, 1}, {2, 2}, {3, 3}, {4, 4}};
    EXPECT_TRUE(BattleMap::isPathStraight(path, 5));
    EXPECT_FALSE(BattleMap::isPathStraight(path, 6));
    EXPECT_TRUE(BattleMap::isPathStraight(path, 3));
  }

  TEST(PounceGeometryTest, BentPathIsNotStraight)
  {
    // An L-shaped path: two steps right then one step up is not straight over its full length.
    CoordVector path{{0, 0}, {1, 0}, {2, 0}, {2, 1}};
    EXPECT_FALSE(BattleMap::isPathStraight(path, 4));
    // ...but its last two coords still form a straight (single-step) segment.
    EXPECT_TRUE(BattleMap::isPathStraight(path, 2));
  }

  // ---------------------------------------------------------------------------
  // Planning across the Wild Shape boundary (mirroring the intent of Python
  // test_basic_wildshape / test_wildshape_with_concentration_spell, adapted to
  // 2024 rules where the druid is never swapped for a separate beast combatant).
  // ---------------------------------------------------------------------------

  // The planner must be able to combine a bonus-action Wild Shape with a beast
  // attack within the same turn (planning across the Wild Shape boundary).
  TEST_F(MoonDruidLvl3Test, PlanCombinesWildshapeAndBeastAttack)
  {
    prepWildshapeForms();
    // Restrict the available forms to the Dire Wolf so the planner has a single, unambiguous
    // shape branch to explore (its Bite is a plain melee attack, unlike the Tiger's straight-line
    // Pounce, making the cross-boundary combination deterministic).
    auto wolf = findForm(DireWolf::getStaticClassId());
    ASSERT_NE(wolf, nullptr);
    druid->setAvailableWildshapeForms({wolf});

    session->addCombatant(druid, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*druid, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{5, 3});

    // Remove the leveled-slot concentration spells so the planner is driven toward
    // shifting into a beast and biting rather than dropping an AoE/control spell.
    druid->getSpellslots().depleteResource(ResourceDepletionLevel::FULLY_DEPLETED);

    auto plan = planFor(druid);

    // The plan spans the boundary: it shapeshifts (bonus action) and then strikes with the
    // grafted beast attack (Bite, +5 1d10+3 — strictly better than the druid's Longbow).
    EXPECT_TRUE(planContains<Wildshape>(plan));
    const bool hasBeastBite = std::any_of(plan.begin(), plan.end(), [](const std::shared_ptr<Actoid> &a)
                                          { return a->toString().rfind("Bite", 0) == 0; });
    EXPECT_TRUE(hasBeastBite);
  }

  // The grafted Pounce must produce positive threat once the druid is in beast form,
  // i.e. the action is plannable across the boundary (not an inert placeholder).
  TEST_F(MoonDruidLvl3Test, PounceThreatPositiveWhileShaped)
  {
    prepWildshapeForms();
    session->addCombatant(druid, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*druid, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{2, 3}); // adjacent

    auto tiger = findForm(Tiger::getStaticClassId());
    ASSERT_NE(tiger, nullptr);
    tiger->activate();

    auto *threat = dynamic_cast<DirectThreatFactory *>(findFactory(druid->getActionFactoriesConst(), AbilityType::POUNCE));
    ASSERT_NE(threat, nullptr);
    EXPECT_GT(threat->calculateThreatToTarget(goblin, {}), 0.0);
  }

  // The Lion's Roar must likewise graft onto the druid and produce positive threat
  // against an enemy within range once the druid takes the Lion form.
  TEST_F(MoonDruidLvl3Test, RoarThreatPositiveWhileShaped)
  {
    prepWildshapeForms();
    session->addCombatant(druid, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*druid, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{3, 3}); // within Roar range (3 cells)

    auto lion = findForm(Lion::getStaticClassId());
    ASSERT_NE(lion, nullptr);
    lion->activate();

    EXPECT_TRUE(hasNamedFactory(druid->getActionFactoriesConst(), "Roar"));
    auto *threat = dynamic_cast<DirectThreatFactory *>(findFactory(druid->getActionFactoriesConst(), AbilityType::ROAR));
    ASSERT_NE(threat, nullptr);
    EXPECT_GT(threat->calculateThreatToTarget(goblin, {}), 0.0);
  }

  // ---------------------------------------------------------------------------
  // Dire Wolf Bite: 2024 Prone rider — automatic (no saving throw), gated on the
  // target being Huge or smaller.
  // ---------------------------------------------------------------------------
  TEST(DireWolfBiteTest, KnocksMediumTargetProneWithoutSave)
  {
    BattleMap::resetInstance();
    Teams::resetInstance();
    EffectTracker::resetInstance();

    DireWolf wolf(1);
    Goblin target(1); // Small/Medium — well within "Huge or smaller".

    OnHitProne rider(Size::HUGE);
    ASSERT_FALSE(rider.requiresSave());
    rider.hit(&wolf, nullptr, &target, 1.0, 0.0);
    EXPECT_TRUE(target.isAffectedBy(Conditions::PRONE));
  }

  TEST(DireWolfBiteTest, DoesNotProneGargantuanTarget)
  {
    BattleMap::resetInstance();
    Teams::resetInstance();
    EffectTracker::resetInstance();

    DireWolf wolf(1);
    Goblin target(1);
    target.setSize(Size::GARGANTUAN); // Larger than Huge — immune to the Prone rider.

    OnHitProne rider(Size::HUGE);
    rider.hit(&wolf, nullptr, &target, 1.0, 0.0);
    EXPECT_FALSE(target.isAffectedBy(Conditions::PRONE));
  }

} // namespace

