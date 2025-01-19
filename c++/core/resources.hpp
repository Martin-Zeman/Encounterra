#pragma once

#include <limits>
#include <optional>

#include "actions/action_types.hpp"
#include "core/interfaces.hpp"
#include "core/state_machine.hpp"

namespace enc
{

  //! @brief This is for importResource and exportResource
  struct ResourceState
  {
    int movement;
    bool hasAction;
    bool hasBonusAction;
    bool hasHasteAction;
    StateId attackFsmState;
    std::unordered_map<AbilityType, int> ammo; // Using AbilityType as key for ammo types

    // Optional resources that only some combatants have
    std::optional<std::unordered_map<int, int>> spellslots; // level -> count
    std::optional<int> channelDivinity;
    std::optional<bool> castLeveledSpellThisTurn;
    std::optional<int> layOnHandsPool;
    std::optional<bool> usedSneakAttackThisTurn;
    // ... other optional resources
  };

  enum class ResourceDepletionLevel
  {
    FULLY_RESTED = 1,
    PARTIALLY_DEPLETED,
    FULLY_DEPLETED
  };

  enum class ResourceRefreshType
  {
    LONG_REST,
    SHORT_REST,
    ROUND,
    NEVER
  };

  class Resource
  {
  public:
    static constexpr int NO_LEVEL = -1;

    Resource(ResourceRefreshType refreshType) : _refreshType(refreshType) {}
    virtual ~Resource() = default;

    virtual bool hasUses(int level = NO_LEVEL) const = 0;
    virtual int getUses(int level = NO_LEVEL) const = 0;
    virtual void useResource(int amount = 1) = 0;
    virtual void reset() = 0;
    virtual void depleteResource(ResourceDepletionLevel level) = 0;

  protected:
    ResourceRefreshType _refreshType;
  };

  class Uses : public Resource
  {
  public:
    static const int INFINITE_USES = std::numeric_limits<int>::max();

    Uses() : Resource(ResourceRefreshType::LONG_REST), _currUses(Uses::INFINITE_USES), _maxUses(Uses::INFINITE_USES) {}
    Uses(int uses, ResourceRefreshType refreshType = ResourceRefreshType::LONG_REST) : Resource(refreshType), _currUses(uses), _maxUses(uses) {}

    bool hasUses(int level = NO_LEVEL) const override { return _currUses > 0; } // level is ignored in this case
    int getUses(int level = NO_LEVEL) const override { return _currUses; }      // level is ignored in this case
    void useResource(int uses = 1) override { _currUses -= uses; }
    void addResource(int uses = 1) { _currUses += uses; }
    void setResource(int uses) { _currUses = uses; }
    bool isInf() const { return _currUses == Uses::INFINITE_USES; }
    void reset() override { _currUses = _maxUses; }

    void depleteResource(ResourceDepletionLevel level) override
    {
      switch(level)
        {
        case ResourceDepletionLevel::FULLY_DEPLETED: _currUses = 0; break;
        case ResourceDepletionLevel::PARTIALLY_DEPLETED: _currUses = _maxUses / 2; break;
        default: break;
        }
    }

  private:
    int _currUses;
    int _maxUses;
  };

  class Combatant;
  
  void useResources(Combatant &combatant, Actoid &actoid);
}