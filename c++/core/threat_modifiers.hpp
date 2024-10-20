#pragma once

#include <unordered_map>
#include <variant>
#include <optional>
#include "core/misc.hpp"

namespace enc{

class ThreatModifiers {
public:
    using ModifierValue = std::variant<int, Die, RollType, bool, std::vector<Die>>;

    void set(ThreatModifierType type, ModifierValue value) {
        _modifiers[type] = value;
    }

    template<typename T>
    std::optional<T> get(ThreatModifierType type) const {
        auto it = _modifiers.find(type);
        if (it != _modifiers.end()) {
            if (const T* value = std::get_if<T>(&it->second)) {
                return *value;
            }
        }
        return std::nullopt;
    }

    template<typename T>
    T getOrDefault(ThreatModifierType type, T defaultValue) const {
        auto value = get<T>(type);
        return value.value_or(defaultValue);
    }

    void clear() { _modifiers.clear(); }

  private:
    std::unordered_map<ThreatModifierType, ModifierValue> _modifiers;
};
}
