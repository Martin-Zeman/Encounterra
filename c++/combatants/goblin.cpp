#include "goblin.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc {
    Goblin(int num) : Combatant(concatName("Goblin", num), 7, 15, 2, 0, 30, 0){
        _type = CombatantType::MONSTER;
        _subtype = Monster;
        _level = 1;
        _id = Combatant::generateUniqueId(_name, _type, _subtype, _level);
    }
    // Goblin(std::string name): Combatant(name, 7, 15, 2, 0, 30, 0){
    //     _name = "Goblin";
    //     _type = CombatantType::MONSTER;
    //     _subtype = Monster;
    //     _level = 1;
    //     _id = Combatant::generateUniqueId(_name, _type, _subtype, _level);
    // }
}