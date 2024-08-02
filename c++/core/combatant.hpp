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

namespace enc {

class ProtoCombatant {};

class Combatant : public ProtoCombatant {
public:
    std::string name;
    ClassType cls;
    int level;
    int id;

    Combatant(int num_or_name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc, 
              std::unordered_set<std::string> resistances = {}, std::vector<std::string> immunities = {}, std::vector<std::string> vulnerabities = {});

    Combatant(std::string num_or_name, int hp, int ac, int init_bonus, int spell_to_hit, int speed, int dc, 
              std::unordered_set<std::string> resistances = {}, std::vector<std::string> immunities = {}, std::vector<std::string> vulnerabities = {});

    static int generateUniqueId(const std::string& name, ClassType cls, int level) {
        std::stringstream ss;
        ss << name << "-" << static_cast<int>(cls) << "-" << level;
        std::string unique_str = ss.str();
        
        unsigned char hash[SHA256_DIGEST_LENGTH];
        SHA256((unsigned char*)unique_str.c_str(), unique_str.size(), hash);
        
        std::stringstream hash_ss;
        for (int i = 0; i < 4; ++i) {
            hash_ss << std::setw(2) << std::setfill('0') << std::hex << static_cast<int>(hash[i]);
        }

        return std::stoul(hash_ss.str(), nullptr, 16);
    }

private:
    std::string nameFromNumber(int num);

    int max_hp;
    int curr_hp;
    int max_hp_modifier = 0;
    int temporary_hp = 0;
    int ac;
    int dc;
    int init_bonus;
    int spell_to_hit;
    int aoo_factory = 0;
    int pam_factory = 0;
    int ability_dmg_bonus = 0;
    int curr_init = 0;
    bool has_action = true;
    bool has_bonus_action = true;
    bool has_reaction = true;
    bool has_haste_action = false;
    std::unordered_map<std::string, int> resources;
    int speed;
    int movement;
    std::unordered_map<std::string, int> ammo;
    std::unordered_set<std::string> resistances;
    std::vector<std::string> immunities;
    std::vector<std::string> vulnerabities;
    // ... Other member variables

    // Example default initializations for vectors and maps
    std::vector<std::pair<Action, std::function<void()>>> action_factories;
    std::pair<Action, std::function<void()>> dodge_factory;
    std::pair<Action, std::function<void()>> disengage_factory;
    std::unordered_map<SavingThrow, int> saving_throws = {
        {SavingThrow::STR, 0}, {SavingThrow::DEX, 0}, {SavingThrow::CON, 0},
        {SavingThrow::INT, 0}, {SavingThrow::WIS, 0}, {SavingThrow::CHA, 0}
    };
    std::unordered_map<SavingThrow, std::vector<int>> saving_throws_flat_mod;
    std::unordered_map<SavingThrow, std::vector<int>> saving_throws_dice_mod;
    std::unordered_map<SavingThrow, std::unordered_set<int>> saving_throws_roll_type_mod;
    std::unordered_set<std::string> dmg_types_took_last_round;
};

}
