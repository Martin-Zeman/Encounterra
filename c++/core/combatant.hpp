#pragma once

#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <random>
#include <iostream>
#include <functional>
#include <sstream>
#include <iomanip>
#include <openssl/sha.h>
#include "misc.hpp"
#include "types.hpp"
#include "interfaces.hpp"

namespace enc
{

  class ProtoCombatant
  {};

  class Combatant : public ProtoCombatant
  {
  public:
    std::string _name;
    CombatantType _type;
    SubType _subtype;
    int _level;
    int _id;

    Combatant(std::string name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc, std::unordered_set<DamageType> resistances = {},
              std::unordered_set<DamageType> immunities = {}, std::unordered_set<DamageType> vulnerabities = {});

    // Combatant(std::string name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc, std::unordered_set<DamageType> resistances =
    // {},
    //           std::unordered_set<DamageType> immunities = {}, std::unordered_set<DamageType> vulnerabities = {});

    static int generateUniqueId(const std::string &name, CombatantType type, const SubType &subtype, int level)
    {
      std::stringstream ss;
      ss << name << "-" << static_cast<int>(type) << "-";

      std::visit([&ss](auto &&arg) { ss << typeid(arg).name(); }, subtype);

      ss << "-" << level;
      std::string unique_str = ss.str();

      unsigned char hash[SHA256_DIGEST_LENGTH];
      SHA256(reinterpret_cast<const unsigned char *>(unique_str.c_str()), unique_str.size(), hash);

      std::stringstream hash_ss;
      for(int i = 0; i < 4; ++i)
        {
          hash_ss << std::setw(2) << std::setfill('0') << std::hex << static_cast<int>(hash[i]);
        }
      return std::stoul(hash_ss.str(), nullptr, 16);
    }

    std::string toString() const;

    bool isAlive() const;

    void onDie();

    void onEndOfTurn();

    void rollInitiative();

    void setSize(Size size) { _size = size; };
    Size getSize() const { return _size; };
    void setTeamColor(Color teamColor) {_teamColor = teamColor;}

    bool hasAction(){return _hasAction;}
    bool hasBonusAction(){return _hasBonusAction;}
    bool hasHasteAction(){return _hasHasteAction;}
    bool hasReaction(){return _hasReaction;}
    int getMeleeReactionRange(){return _meleeReactionRange;}

  private:
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

  protected:
    Size _size{Size::MEDIUM};
  };

}
