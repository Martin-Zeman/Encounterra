#pragma once

#include "core/types.hpp"
#include <map>
#include <cstdint>
#include <variant>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace enc
{
  // enum class Artificer
  // {
  //   ALCHEMIST,
  //   ARMORER,
  //   ARTILLERIST,
  //   BATTLE_SMITH
  // };

  enum class Barbarian
  {
    PATH_OF_THE_BERSERKER,
    PATH_OF_THE_ZEALOT,
    PATH_OF_WILD_HEART,
    PATH_OF_WORLD_TREE,
    BEFORE_SUBCLASS
  };

  enum class Bard
  {
    COLLEGE_OF_DANCE,
    COLLEGE_OF_GLAMOUR,
    COLLEGE_OF_LORE,
    COLLEGE_OF_VALOR,
    BEFORE_SUBCLASS
  };

  enum class Cleric
  {
    LIFE_DOMAIN,
    LIGHT_DOMAIN,
    TRICKERY_DOMAIN,
    WAR_DOMAIN,
    BEFORE_SUBCLASS
  };

  enum class Druid
  {
    CIRCLE_OF_LAND,
    CIRCLE_OF_MOON,
    CIRCLE_OF_SEA,
    CIRCLE_OF_STARS,
    BEFORE_SUBCLASS
  };

  enum class Fighter
  {
    BATTLE_MASTER,
    ELDRITCH_KNIGHT,
    PSI_WARRIOR,
    CHAMPION,
    BEFORE_SUBCLASS
  };

  enum class Paladin
  {
    OATH_OF_DEVOTION,
    OATH_OF_GLORY,
    OATH_OF_ANCIENTS,
    OATH_OF_VENGEANCE,
    BEFORE_SUBCLASS
  };

  enum class Ranger
  {
    BEAST_MASTER,
    FEY_WANDERER,
    GLOOM_STALKER,
    HUNTER,
    BEFORE_SUBCLASS
  };

  enum class Rogue
  {
    ARCANE_TRICKSTER,
    ASSASSIN,
    SOULKNIFE,
    THIEF,
    BEFORE_SUBCLASS
  };

  enum class Monk
  {
    WARRIOR_OF_MERCY,
    WARRIOR_OF_SHADOW,
    WARRIOR_OF_THE_OPEN_HAND,
    WARRIOR_OF_THE_ELEMENTS,
    BEFORE_SUBCLASS
  };

  enum class Sorcerer
  {
    ABERRANT_SORCERY,
    CLOCKWORK_SORCERY,
    DRACONIC_SORCERY,
    WILD_MAGIC,
    BEFORE_SUBCLASS
  };

  enum class Warlock
  {
    ARCHFEY_PATRON,
    CELESTIAL_PATRON,
    FIEND_PATRON,
    GREAT_OLD_ONE_PATRON,
    UNDYING
  };

  enum class Wizard
  {
    ABJURER,
    DIVINER,
    EVOKER,
    ILLUSIONIST,
    BEFORE_SUBCLASS
  };

  enum class Monster
  {
    HUMANOID,
    GIANT,
    MONSTROSITY,
    BEAST,
    UNDEAD,
    DRAGON,
    CONSTRUCT,
    ELEMENTAL,
    ABERRATION,
    FEY,
    OOZE,
    PLANT,
    FIEND
  };

  enum class CombatantType
  {
    // ARTIFICER,
    BARBARIAN,
    BARD,
    CLERIC,
    DRUID,
    FIGHTER,
    PALADIN,
    RANGER,
    ROGUE,
    MONK,
    SORCERER,
    WARLOCK,
    WIZARD,
    MONSTER
  };

  using SubType = std::variant<Monster, Barbarian, Bard, Cleric, Druid, Fighter, Paladin, Rogue, Ranger, Monk, Sorcerer, Warlock, Wizard>;

  enum class SpellcastingResourceType
  {
    SPELLSLOTS,
    SPECIAL
  };

  enum class SavingThrow
  {
    STR = 1,
    DEX,
    CON,
    INT,
    WIS,
    CHA
  };

  enum class SkillCheck
  {
    ATHLETICS = 1,
    ACROBATICS
  };

  enum class DamageType
  {
    Bludgeoning = 0,
    Slashing,
    Piercing,
    Fire,
    Cold,
    Poison,
    Acid,
    Lightning,
    Radiant,
    Necrotic,
    Force,
    Psychic,
    Thunder,
    Random,
    Original // used for DamageType override
  };

  const std::unordered_map<DamageType, std::string> DAMAGE_TYPE_TO_STRING = {
    {DamageType::Bludgeoning, "Bludgeoning"},
    {DamageType::Slashing, "Slashing"},
    {DamageType::Piercing, "Piercing"},
    {DamageType::Fire, "Fire"},
    {DamageType::Cold, "Cold"},
    {DamageType::Poison, "Poison"},
    {DamageType::Acid, "Acid"},
    {DamageType::Lightning, "Lightning"},
    {DamageType::Radiant, "Radiant"},
    {DamageType::Necrotic, "Necrotic"},
    {DamageType::Force, "Force"},
    {DamageType::Psychic, "Psychic"},
    {DamageType::Thunder, "Thunder"},
    {DamageType::Random, "Random"},
  };

  using DmgDieWithType = std::pair<Die, DamageType>;

  enum class Size
  {
    TINY = -2,
    SMALL = -1,
    MEDIUM = 0,
    LARGE = 1,
    HUGE = 2,
    GARGANTUAN = 3,
    CUSTOM = 4 // only used for cases where Coords express a set of coordinates that's not a combatant
  };

  //! 2024 weapon mastery properties. A weapon grants its mastery to a proficient wielder.
  enum class WeaponMastery
  {
    NONE,
    CLEAVE, //!< On hit, make one extra attack against a second enemy within 5 ft (once per turn).
    GRAZE,  //!< On a miss, deal damage equal to the ability modifier used for the attack.
    NICK,   //!< The Light extra attack can be made as part of the Attack action (no Bonus Action cost).
    PUSH,   //!< On hit, push a Large-or-smaller target up to 10 ft away.
    SAP,    //!< On hit, the target has Disadvantage on its next attack roll before the wielder's next turn.
    SLOW,   //!< On hit, reduce the target's Speed by 10 ft until the start of the wielder's next turn.
    TOPPLE, //!< On hit, the target makes a Con save or has the Prone condition.
    VEX     //!< On hit, the wielder has Advantage on its next attack roll against that target.
  };

  enum class Statistics
  {
    VICTORIES = 1,
    AT_LEAST_ONE_DIED = 2,
    AT_LEAST_TWO_DIED = 3,
    AT_LEAST_THREE_DIED = 4
  };

  struct RollResult
  {
    int sum;
    std::vector<std::pair<int, int>> rerollLog; // pairs of (original, reroll)
  };

  struct ChaosBoltResult
  {
    int sum;
    std::vector<int> numbersRolled;
  };

  // Helper function to get all statistics for iteration
  inline std::vector<Statistics> getAllStatistics()
  {
    return {Statistics::VICTORIES, Statistics::AT_LEAST_ONE_DIED, Statistics::AT_LEAST_TWO_DIED, Statistics::AT_LEAST_THREE_DIED};
  }

  enum class PhaseOfTurn
  {
    START_OF_TURN,
    END_OF_TURN,
    ACTION
  };

  enum class Side
  {
    ENEMY,
    ALLY
  };  
  
  enum class DistanceMetric
  {
    HOP,
    CARTESIAN
  };

  enum class RollType : uint8_t
  {
    STRAIGHT,
    ADVANTAGE,
    DISADVANTAGE
  };

  inline RollType operator|(RollType a, RollType b) { return static_cast<RollType>(static_cast<uint8_t>(a) | static_cast<uint8_t>(b)); }

  // inline RollType operator&(RollType a, RollType b) { return static_cast<RollType>(static_cast<uint8_t>(a) & static_cast<uint8_t>(b)); }

  const std::unordered_map<RollType, std::map<int, int>> ROLL_TYPE_DELTA
    = {{RollType::STRAIGHT, {{1, 0},  {2, 0},  {3, 0},  {4, 0},  {5, 0},  {6, 0},  {7, 0},  {8, 0},  {9, 0},  {10, 0},
                             {11, 0}, {12, 0}, {13, 0}, {14, 0}, {15, 0}, {16, 0}, {17, 0}, {18, 0}, {19, 0}, {20, 0}}},
       {RollType::ADVANTAGE, {{1, 0},  {2, 1},  {3, 2},  {4, 3},  {5, 3},  {6, 4},  {7, 4},  {8, 5},  {9, 5},  {10, 5},
                              {11, 5}, {12, 5}, {13, 5}, {14, 5}, {15, 4}, {16, 4}, {17, 3}, {18, 3}, {19, 2}, {20, 1}}},
       {RollType::DISADVANTAGE, {{1, 0},   {2, -1},  {3, -2},  {4, -3},  {5, -3},  {6, -4},  {7, -4},  {8, -5},  {9, -5},  {10, -5},
                                 {11, -5}, {12, -5}, {13, -5}, {14, -5}, {15, -4}, {16, -4}, {17, -3}, {18, -3}, {19, -2}, {20, -1}}}};

  // Function to safely get the delta value
  int getRollTypeDelta(RollType rollType, int rollNeeded, int defaultValue = 0);

  RollType reconcileRollTypes(const std::unordered_set<RollType> &types);

  std::vector<int> generateOutcomes(const Die &die);

  int findPercentileValue(const std::vector<int> &outcomes, int percentile);

  int percentileRoll(const Die &die, int percentile);

  double percentOfCurrHp(double curr_hp, double dmg);

  double avgRoll(const Die& die);

  double avgRollMulti(const std::vector<Die> &dice);

  double
  meanDmg(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, bool isImmune = false, bool isResistant = false, int critRange = 1);

  double calcPHit(int toHit, int ac);

  double meanDmgDcAttack(int dc, const std::vector<Die> &dmgDice, bool halfOnSuccess, int stBonus, bool isImmune = false, bool isResistant = false);

  double meanDmgAutoHit(const std::vector<Die> &dmgDice, bool isImmune = false, bool isResistant = false);

  int rollDice(const Die &dice);

  int rollDiceMulti(const std::vector<Die> &diceList);

  int rollDiceWithReroll(const Die &die, int rerollMaxValue);

  //! Roll a die group applying a per-die floor: any die result below @p floorValue counts as @p floorValue.
  //! Used by the 2024 Great Weapon Fighting style ("treat any 1 or 2 on a damage die as a 3").
  int rollDiceWithFloor(const Die &die, int floorValue);

  //! Battle Master Superiority Die by Fighter level (d8 at 3-9, d10 at 10-17, d12 at 18-20).
  Die getSuperiorityDie(int level);

  //! Number of Battle Master Superiority Dice by Fighter level (4 at 3-6, 5 at 7-14, 6 at 15+).
  int getSuperiorityDiceCount(int level);

  bool rollSavingThrow(int bonus, int dc, RollType rollType);

  //! Roll a single d20, applying Advantage (highest of two) or Disadvantage (lowest of two).
  int rollD20(RollType rollType);

  bool rollAbilityCheck(int bonus, int dc, RollType rollType);

  ChaosBoltResult rollDiceChaosBolt(const Die &die);

  std::pair<int, std::vector<int>> rollChaosBoltDmg(const DmgDieWithType &dmgDice, const Die &additionalDmgDice);

  const std::map<RollType, double> ROLL_TYPE_CRIT_DELTA = {{RollType::STRAIGHT, 1.0}, {RollType::ADVANTAGE, 2.0}, {RollType::DISADVANTAGE, 0.5}};

  std::string coordToString(const Coord& coord);

  enum class ThreatModifierType
  {
    TO_HIT_FLAT,
    TO_HIT_DIE,
    ROLL_TYPE,
    RANGE,
    DMG_BONUS_FLAT,
    DMG_BONUS_DIE,
    CRIT_RANGE,
    AUTO_CRIT,
    TARGET_AC,
    SAVE_DC //!< Flat bonus to the caster's spell save DC (e.g. Innate Sorcery's +1), used by save-based spells.
  };

  enum class Terrain
  {
    NORMAL_TERRAIN = 0,
    DIFFICULT_TERRAIN,
    IMPASSABLE_TERRAIN
  };

  enum class Occupancy
  {
    FREE = 1,
    OCCUPIED_BY_COMBATANT
  };

  enum class Visibility
  {
    NONE = 0,
    THREE_QUARTERS_COVER,
    HALF_COVER,
    FULL
  };

  const double THREE_QUARTERS_COVER_ERROR_THRESHOLD = 0.25;
  const double HALF_COVER_ERROR_THRESHOLD = 0.35;
  const double FULL_VISIBILITY_ERROR_THRESHOLD = 0.45;
}
