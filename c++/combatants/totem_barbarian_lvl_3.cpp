#include "totem_barbarian_lvl_3.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc {
    TotemBarbarianLvl3::TotemBarbarianLvl3(int num) : Combatant(concatName("Totem Barbarian LVL 3", num), 35, 14, 1, 0, 30, 13){
        _type = CombatantType::BARBARIAN;
        _subtype = Barbarian::PATH_OF_THE_TOTEM_WARRIOR;
        _level = 1;
        _id = Combatant::generateUniqueId(_name, _type, _subtype, _level);
    }
}