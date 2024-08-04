#include "draconic_sorcerer_lvl_1.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc {
    DraconicSorcererLvl1::DraconicSorcererLvl1(int num) : Combatant(concatName("DraconicSorcerer LVL 1", num), 7, 15, 2, 0, 30, 0){
        _type = CombatantType::SORCERER;
        _subtype = Sorcerer::BEFORE_SUBCLASS;
        _level = 1;
        _id = Combatant::generateUniqueId(_name, _type, _subtype, _level);
    }
}