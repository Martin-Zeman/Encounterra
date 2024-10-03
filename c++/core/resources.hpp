#pragma once

#include <limits>

#include "actions/action_types.hpp"
#include "core/interfaces.hpp"

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

    virtual void useResource(int amount = 1) = 0;
    virtual void reset() = 0;
    virtual void depleteResource(ResourceDepletionLevel level) = 0;

  protected:
    ResourceRefreshType _refreshType;
  };

  class LeveledResource : public Resource
  {
  public:
    LeveledResource(ResourceRefreshType refreshType) : Resource(refreshType) {}
    virtual bool hasUses(int level) const = 0;
    virtual int getUses(int level) const = 0;
  };

  class UnleveledResource : public Resource
  {
  public:
    UnleveledResource(ResourceRefreshType refreshType) : Resource(refreshType) {}
    virtual bool hasUses() const = 0;
    virtual int getUses() const = 0;
  };

  class Uses : public UnleveledResource
  {
  public:
    static const int INFINITE_USES = std::numeric_limits<int>::max();

    Uses() : UnleveledResource(ResourceRefreshType::LONG_REST), _currUses(Uses::INFINITE_USES), _maxUses(Uses::INFINITE_USES) {}
    Uses(int uses, ResourceRefreshType refreshType = ResourceRefreshType::LONG_REST) : UnleveledResource(refreshType), _currUses(uses), _maxUses(uses) {}

    bool hasUses() const override { return _currUses > 0; } // level is ignored in this case
    int getUses() const override { return _currUses; }      // level is ignored in this case
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
  
  void useResources(Combatant *combatant, Actoid &actoid);
}