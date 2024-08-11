#include "bugbear.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc {
    Bugbear::Bugbear(int num) : Combatant(concatName("Bugbear", num), 27, 16, 2, 0, 30, 0){
        _type = CombatantType::MONSTER;
        _subtype = Monster::HUMANOID;
        _level = 1;
        _id = Combatant::generateUniqueId(_name, _type, _subtype, _level);
    }
}