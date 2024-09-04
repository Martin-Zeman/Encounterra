#pragma once

#include "core/interfaces.hpp"
#include "core/misc.hpp"

namespace enc{

    class OnHit{
        virtual std::vector<std::pair<int, DamageType>> hit(ICombatant* attacker, Actoid* attack,  ICombatant* target, double multiplier, double dmgSoFar) = 0;
        virtual double calculateThreat(ICombatant* attacker, ICombatant* target) = 0;
    };
}