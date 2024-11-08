#pragma once

#include "effects/spheric_aoe.hpp"
#include "effects/aoe_effect.hpp"

namespace enc{
class AoeSphericEffect : public SphericAoe, public AoeEffect {
public:
    AoeSphericEffect(Combatant* initiator, const Coord& coord, int radius)
        : SphericAoe(coord, radius)
        , AoeEffect(initiator)
    {}

    // Implement pure virtual methods from Effect base class
    EffectType getEffectType() const override {
        // Return appropriate effect type
        return EffectType::HUNGER_OF_HADAR;  // Or other appropriate type
    }

    void activate(const Kwargs& kwargs = {}) override {
        // Implementation
    }

    void deactivate() override {
        // Implementation
    }

    bool deactivateForCombatant(Combatant* combatant) override {
        // Implementation
        return true;
    }

    bool isAffecting(Combatant* combatant) const override {
        // Implementation
        return false;
    }
};
}
