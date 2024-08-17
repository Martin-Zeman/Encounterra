#include "stone_giant.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc {
    StoneGiant::StoneGiant(int num) : Combatant(concatName("Stone Giant", num), 126, 17, 2, 0, 40, 17){
        _type = CombatantType::MONSTER;
        _subtype = Monster::GIANT;
        _level = 1;
        _id = Combatant::generateUniqueId(_name, _type, _subtype, _level);
        _size = Size::HUGE;
    }
}