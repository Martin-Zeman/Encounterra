#pragma once

#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <random>
#include <iostream>
#include <functional>
#include <sstream>
#include <string_view>
#include <cstdint>
#include <iomanip>
#include <openssl/sha.h>
#include "misc.hpp"
#include "types.hpp"
#include "interfaces.hpp"
#include "conditions.hpp"
#include "resources.hpp"
#include "spellslots.hpp"
#include "actions/action_types.hpp"
#include "actions/action_constants.hpp"

namespace enc
{

  using FactoryCreator = std::function<std::shared_ptr<ActoidFactory>()>;

  class Combatant : public ICombatant
  {
  public:
    std::string _name;
    int _instanceId;

    Combatant(CombatantType type, SubType subtype, int level, std::string name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc,
              std::unordered_set<DamageType> resistances = {}, std::unordered_set<DamageType> immunities = {},
              std::unordered_set<DamageType> vulnerabities = {});

    // Combatant(std::string name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc, std::unordered_set<DamageType> resistances =
    // {},
    //           std::unordered_set<DamageType> immunities = {}, std::unordered_set<DamageType> vulnerabities = {});

    static constexpr uint32_t fnv1a_32(uint32_t initial, uint32_t value)
    {
      uint32_t hash = initial;
      for(int i = 0; i < 32; i += 8)
        {
          hash ^= (value >> i) & 0xFF;
          hash *= 16777619u;
        }
      return hash;
    }

    static constexpr uint32_t fnv1a_32(std::string_view str)
    {
      uint32_t hash = 2166136261u;
      for(char c : str)
        {
          hash ^= static_cast<uint32_t>(c);
          hash *= 16777619u;
        }
      return hash;
    }

    template <typename SubType> static constexpr int generateClassId(std::string_view className, SubType subtype, int level)
    {
      uint32_t hash = fnv1a_32(className);
      hash = fnv1a_32(hash, static_cast<uint32_t>(subtype));
      hash = fnv1a_32(hash, static_cast<uint32_t>(level));
      return static_cast<int>(hash);
    }

    // Method to generate instance ID
    int generateInstanceId() const
    {
      static int nextId = 1;
      return ++nextId;
    }

    std::string toString() const;
    void setShortCode(const std::string &shortCode) { _shortCode = shortCode; }
    std::string getShortCode() const { return _shortCode; }
    virtual int getClassId() const = 0;

    bool isAlive() const;

    void onDie();

    void onEndOfTurn();

    void rollInitiative();

    void setSize(Size size) { _size = size; };
    Size getSize() const { return _size; };
    void setTeamColor(Color teamColor) { _teamColor = teamColor; }

    bool hasAction() { return _hasAction; }
    bool hasBonusAction() { return _hasBonusAction; }
    bool hasHasteAction() { return _hasHasteAction; }
    bool hasReaction() { return _hasReaction; }
    int getMeleeReactionRange() { return _meleeReactionRange; }
    Combatant *getCurrentForm();
    Combatant *getOriginalForm();
    const Combatant *getSwallower() const { return _swallower; }
    void setSwallower(Combatant *swallower) { _swallower = swallower; }
    bool isSwallowed() const { return _swallower != nullptr; }
    const std::vector<Condition> &getConditions() const { return _conditions; }
    const std::vector<ConditionWithDC> &getDCConditions() const { return _dcConditions; }
    bool isAffectedBy(Conditions condition) const;
    void applyCondition(const Condition &condition);
    void applyDCCondition(const ConditionWithDC &dcCondition);
    bool removeCondition(Conditions condition, const Combatant *initiator = nullptr);
    bool removeDCCondition(Conditions condition, const Combatant *initiator = nullptr);
    void removeAllConditionsOfType(Conditions condition);
    Combatant *getInitiatorOfCondition(Conditions condition);
    Combatant *getGrappledTarget();
    std::optional<ConditionWithDC> needsToBreakOutOfGrapple();
    void breakOutOfGrapple();
    bool isAffectedByAny(const std::vector<Conditions> &conditions);
    void setResourceDepletionLevel(ResourceDepletionLevel level) { _resouceDepletionLevel = level; }

    template <typename... Args> std::shared_ptr<ActoidFactory> addAbility(AbilityType abilityType, Args &&...args)
    {
      std::shared_ptr<ActoidFactory> factory;

      switch(abilityType)
        {
          // Action
          case AbilityType::MELEE_ATTACK: {
            factory = std::make_shared<MeleeAttackFactory>(std::forward<Args>(args)...);
          }
          break;
          case AbilityType::RANGED_ATTACK: {
            factory = std::make_shared<RangedAttackFactory>(std::forward<Args>(args)...);
          }
          break;
        case AbilityType::RECKLESS_ATTACK: break;
        case AbilityType::PRE_SWALLOW_BITE: break;
        case AbilityType::BITE_AND_SWALLOW: break;
        case AbilityType::DODGE: break;
        case AbilityType::DASH: break;
        case AbilityType::DISENGAGE: break;
        case AbilityType::FIREBALL: break;
        case AbilityType::FIREBOLT: break;
        case AbilityType::CHAOSBOLT: break;
        case AbilityType::HASTE: break;
        case AbilityType::HUNGER_OF_HADAR: break;
        case AbilityType::SPIKE_GROWTH: break;
        case AbilityType::CLOUD_OF_DAGGERS: break;
        case AbilityType::HIDE: break;
        case AbilityType::TWINNED_FIREBOLT: break;
        case AbilityType::TWINNED_HASTE: break;
        case AbilityType::SCORCHING_RAY: break;
        case AbilityType::FAERIE_FIRE: break;
        case AbilityType::WILDSHAPE: break;
        case AbilityType::POUNCE: break;
        case AbilityType::CONSTRICT: break;
        case AbilityType::BREAK_GRAPPLE: break;
        case AbilityType::FLAMING_SPHERE: break;
        case AbilityType::WEB: break;
        case AbilityType::HOLD_PERSON: break;
        case AbilityType::TWINNED_HOLD_PERSON: break;
        case AbilityType::SHOCKING_GRASP: break;
        case AbilityType::TWINNED_SHOCKING_GRASP: break;
        case AbilityType::MAGIC_MISSILE: break;
        case AbilityType::GRAPPLE: break;
        case AbilityType::GRAPPLE_ATTACK: break;
        case AbilityType::VAMPIRIC_BITE: break;
        case AbilityType::BLESS: break;
        case AbilityType::RAY_OF_ENFEEBLEMENT: break;
        case AbilityType::TWINNED_RAY_OF_ENFEEBLEMENT: break;
        case AbilityType::SLEEP: break;
        case AbilityType::SHAKE_ALLY_AWAKE: break;
        case AbilityType::THUNDERWAVE: break;
        case AbilityType::MENACING_MELEE_ATTACK: break;
        case AbilityType::PARALYZING_MELEE_ATTACK: break;
        case AbilityType::MENACING_RANGED_ATTACK: break;
        case AbilityType::PRECISION_ATTACK: break;
        case AbilityType::LAY_ON_HANDS: break;
        case AbilityType::CURE_WOUNDS: break;
        case AbilityType::ABJURE_ENEMY: break;
        case AbilityType::CONIC_BREATH_WEAPON: break;
        case AbilityType::CONIC_BREATH_WEAPON_ATTACK: break;
        case AbilityType::LINE_BREATH_WEAPON: break;
        case AbilityType::RAY_OF_FROST: break;

        // Bonus Action
        case AbilityType::BONUS_MELEE_ATTACK: break;
        case AbilityType::BONUS_RANGED_ATTACK: break;
        case AbilityType::PAM_BONUS_ATTACK: break;
        case AbilityType::RAGE: break;
        case AbilityType::TOTEM_RAGE: break;
        case AbilityType::MISTY_STEP: break;
        case AbilityType::CUNNING_DISENGAGE: break;
        case AbilityType::CUNNING_DASH: break;
        case AbilityType::CUNNING_HIDE: break;
        case AbilityType::QUICKENED_FIREBALL: break;
        case AbilityType::QUICKENED_FIREBOLT: break;
        case AbilityType::QUICKENED_CHAOSBOLT: break;
        case AbilityType::QUICKENED_HASTE: break;
        case AbilityType::QUICKENED_HUNGER_OF_HADAR: break;
        case AbilityType::QUICKENED_SPIKE_GROWTH: break;
        case AbilityType::QUICKENED_CLOUD_OF_DAGGERS: break;
        case AbilityType::QUICKENED_SCORCHING_RAY: break;
        case AbilityType::QUICKENED_FAERIE_FIRE: break;
        case AbilityType::QUICKENED_BLESS: break;
        case AbilityType::QUICKENED_FLAMING_SPHERE: break;
        case AbilityType::QUICKENED_HOLD_PERSON: break;
        case AbilityType::QUICKENED_RAY_OF_FROST: break;
        case AbilityType::FLAMING_SPHERE_RAM: break;
        case AbilityType::MOON_WILDSHAPE: break;
        case AbilityType::QUICKENED_SHOCKING_GRASP: break;
        case AbilityType::QUICKENED_MAGIC_MISSILE: break;
        case AbilityType::QUICKENED_RAY_OF_ENFEEBLEMENT: break;
        case AbilityType::QUICKENED_SLEEP: break;
        case AbilityType::SECOND_WIND: break;
        case AbilityType::HEALING_WORD: break;
        case AbilityType::TWINNED_HEALING_WORD: break;
        case AbilityType::SHILLELAGH: break;
        case AbilityType::QUICKENED_THUNDERWAVE: break;
        case AbilityType::BONUS_MENACING_MELEE_ATTACK: break;
        case AbilityType::BONUS_MENACING_RANGED_ATTACK: break;
        case AbilityType::SHIELD_OF_FAITH: break;
        case AbilityType::QUICKENED_CURE_WOUNDS: break;
        case AbilityType::VOW_OF_ENMITY: break;
        case AbilityType::AGGRESSIVE: break;

        // Reaction
        case AbilityType::REACTION_ATTACK: break;
        case AbilityType::SHIELD: break;
        case AbilityType::PRE_SWALLOW_BITE_REACTION: break;
        case AbilityType::UNCANNY_DODGE: break;
        case AbilityType::PARRY: break;
        case AbilityType::RIPOSTE: break;
        case AbilityType::REACTION_PARALYZING_MELEE_ATTACK: break;

        // Haste Action
        case AbilityType::HASTE_MELEE_ATTACK: break;
        case AbilityType::HASTE_RANGED_ATTACK: break;
        case AbilityType::HASTE_DASH: break;
        case AbilityType::HASTE_DISENGAGE: break;
        case AbilityType::HASTE_HIDE: break;
        case AbilityType::HASTE_PRE_SWALLOW_BITE: break;
        case AbilityType::HASTE_BITE_AND_SWALLOW: break;
        case AbilityType::HASTE_GRAPPLE_ATTACK: break;
        case AbilityType::HASTE_GRAPPLE: break;
        case AbilityType::HASTE_VAMPIRIC_BITE: break;
        case AbilityType::HASTE_PARALYZING_MELEE_ATTACK: break;

        // Passive
        case AbilityType::SPELLCASTING: break;
        case AbilityType::SENTINEL: break;
        case AbilityType::POLEARM_MASTER: break;
        case AbilityType::DANGER_SENSE: break;
        case AbilityType::METAMAGIC: break;
        case AbilityType::PACK_TACTICS: break;
        case AbilityType::FANATIC_ADVANTAGE: break;
        case AbilityType::WAR_CASTER: break;
        case AbilityType::ELDRITCH_MIND: break;
        case AbilityType::SNEAK_ATTACK: break;
        case AbilityType::CUNNING_ACTION: break;
        case AbilityType::ASSASSINATE: break;
        case AbilityType::REGENERATION: break;
        case AbilityType::EVASION: break;
        case AbilityType::HEART_OF_HRUGGEK: break;
        case AbilityType::DARK_DEVOTION: break;
        case AbilityType::BLINDSIGHT: break;
        case AbilityType::MAGIC_RESISTANCE: break;
        case AbilityType::CHARM_IMMUNITY: break;
        case AbilityType::GREAT_WEAPON_FIGHTING: break;
        case AbilityType::DUELING: break;
        case AbilityType::BATTLE_MASTER_MANEUVERS: break;
        case AbilityType::DRACONIC_RESILIENCE: break;
        case AbilityType::UNARMORED_DEFENSE: break;
        case AbilityType::DIVINE_SMITE: break;
        case AbilityType::CHANNEL_DIVINITY: break;
        case AbilityType::UNDEAD_FORTITUDE: break;
        case AbilityType::MARTIAL_ADVANTAGE: break;

        // Meta Action
        case AbilityType::QUICKENED_SPELL: break;
        case AbilityType::TWINNED_SPELL: break;
        case AbilityType::EMPOWERED_SPELL: break;

        // Free Action
        case AbilityType::ACTION_SURGE: break;

          default: {
            throw std::runtime_error("Unknown ability type");
          }
          break;
        }

      return factory;
    }

  private:
    template <typename ConditionType> Combatant *checkConditionList(const std::vector<ConditionType> &condList, Conditions condition) const
    {
      for(const auto &cond : condList)
        {
          if(containsCondition(cond.conditionComposite, condition))
            {
              return cond.initiator;
            }
        }
      return nullptr;
    }

    std::string _shortCode;
    int _maxHp;
    int _currHp;
    int _maxHpModifier = 0;
    int _temporaryHp = 0;
    int _ac;
    int _dc;
    int _initBonus;
    int _spellToHit;
    int _aooFactory = 0;
    int _pamFactory = 0;
    int _abilityDmgBonus = 0;
    int _currInit = 0;
    bool _hasAction = true;
    bool _hasBonusAction = true;
    bool _hasReaction = true;
    bool _hasHasteAction = false;
    int _meleeReactionRange = 1;
    int _speed;
    int _movement;
    Color _teamColor;
    std::unordered_map<std::string, int> _ammo;
    std::unordered_set<DamageType> _resistances;
    std::unordered_set<DamageType> _immunities;
    std::unordered_set<DamageType> _vulnerabities;
    // ... Other member variables

    std::shared_ptr<ActoidFactory> _dodgeFactory;
    std::shared_ptr<ActoidFactory> _disengageFactory;
    std::vector<std::shared_ptr<ActoidFactory>> _actionFactories;
    std::vector<std::shared_ptr<ActoidFactory>> _bonusActionFactories;
    std::vector<std::shared_ptr<ActoidFactory>> _reactionFactories;
    std::vector<std::shared_ptr<ActoidFactory>> _hasteActionFactories;
    std::vector<AbilityType> _passiveAbilities;
    std::unordered_map<SavingThrow, int> _savingThrows
      = {{SavingThrow::STR, 0}, {SavingThrow::DEX, 0}, {SavingThrow::CON, 0}, {SavingThrow::INT, 0}, {SavingThrow::WIS, 0}, {SavingThrow::CHA, 0}};
    std::unordered_map<SavingThrow, std::vector<int>> _savingThrowsFlatMod;
    std::unordered_map<SavingThrow, std::vector<Die>> _savingThrowsDiceMod;
    std::unordered_map<SavingThrow, std::unordered_set<RollType>> _savingThrowsRollTypeMod;
    std::unordered_set<std::string> _dmgTypesTookLastRound;
    Combatant *_originalForm = this;
    Combatant *_currentWildshapeForm = nullptr;
    Combatant *_swallower = nullptr;
    Combatant *_swallowedTarget = nullptr;
    std::vector<Condition> _conditions;
    std::vector<ConditionWithDC> _dcConditions;
    ResourceDepletionLevel _resouceDepletionLevel;
    std::shared_ptr<Spellslots> _spellslots;
    std::unordered_map<AbilityType, std::shared_ptr<Resource>> _resources;

  protected:
    Size _size{Size::MEDIUM};
    int _classId;
    // int _instanceId;
    CombatantType _type;
    SubType _subtype;
    int _level;
  };

}
