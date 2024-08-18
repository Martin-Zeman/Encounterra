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

namespace enc
{

  class ProtoCombatant
  {};

  class Combatant : public ProtoCombatant
  {
  public:
    std::string _name;
    // CombatantType _type;
    // SubType _subtype;
    // int _level;
    int _id;

    Combatant(CombatantType type, SubType subtype, int level, std::string name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc, std::unordered_set<DamageType> resistances = {},
              std::unordered_set<DamageType> immunities = {}, std::unordered_set<DamageType> vulnerabities = {});

    // Combatant(std::string name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc, std::unordered_set<DamageType> resistances =
    // {},
    //           std::unordered_set<DamageType> immunities = {}, std::unordered_set<DamageType> vulnerabities = {});


    static constexpr uint32_t fnv1a_32(uint32_t initial, uint32_t value) {
        uint32_t hash = initial;
        for (int i = 0; i < 32; i += 8) {
            hash ^= (value >> i) & 0xFF;
            hash *= 16777619u;
        }
        return hash;
    }

    static constexpr uint32_t fnv1a_32(std::string_view str) {
        uint32_t hash = 2166136261u;
        for (char c : str) {
            hash ^= static_cast<uint32_t>(c);
            hash *= 16777619u;
        }
        return hash;
    }

    template<typename SubType>
    static constexpr int generateClassId(std::string_view className, SubType subtype, int level) {
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
    void setShortCode(std::string&& shortCode ){_shortCode = std::move(shortCode);}
    std::string getShortCode(){ return _shortCode;}

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
    const Combatant* getSwallower() const { return _swallower; }
    void setSwallower(Combatant* swallower) { _swallower = swallower; }
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
    std::unordered_map<std::string, int> _resources;
    int _speed;
    int _movement;
    Color _teamColor;
    std::unordered_map<std::string, int> _ammo;
    std::unordered_set<DamageType> _resistances;
    std::unordered_set<DamageType> _immunities;
    std::unordered_set<DamageType> _vulnerabities;
    // ... Other member variables

    std::shared_ptr<Factory> _dodgeFactory;
    std::shared_ptr<Factory> _disengageFactory;
    std::vector<std::shared_ptr<Factory>> _actionFactories;
    std::unordered_map<SavingThrow, int> _savingThrows
      = {{SavingThrow::STR, 0}, {SavingThrow::DEX, 0}, {SavingThrow::CON, 0}, {SavingThrow::INT, 0}, {SavingThrow::WIS, 0}, {SavingThrow::CHA, 0}};
    std::unordered_map<SavingThrow, std::vector<int>> _savingThrowsFlatMod;
    std::unordered_map<SavingThrow, std::vector<Die>> _savingThrowsDiceMod;
    std::unordered_map<SavingThrow, std::unordered_set<RollType>> _savingThrowsRollTypeMod;
    std::unordered_set<std::string> _dmgTypesTookLastRound;
    Combatant *_originalForm = this;
    Combatant *_currentWildshapeForm = nullptr;
    Combatant* _swallower = nullptr;
    Combatant* _swallowedTarget = nullptr;
    std::vector<Condition> _conditions;
    std::vector<ConditionWithDC> _dcConditions;
    ResourceDepletionLevel _resouceDepletionLevel;

  protected:
    Size _size{Size::MEDIUM};
    int _classId;
    int _instanceId;
    CombatantType _type;
    SubType _subtype;
    int _level;
  };

}
