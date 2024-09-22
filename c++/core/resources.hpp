#pragma once

#include <limits>

namespace enc
{

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
    Resource(ResourceRefreshType refreshType) : _refreshType(refreshType) {}
    virtual ~Resource() = default;

    virtual bool hasResource(int level) const = 0;
    virtual int getResource(int level) const = 0;
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

    bool hasResource(int level) const override { return _currUses > 0; } // level is ignored in this case
    int getResource(int level) const override { return _currUses; }      // level is ignored in this case
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
  
  void useResources(Combatant *combatant, AbilityType abilityType);
}