#include <vector>
#include <optional>
#include <algorithm>
#include "combatant.hpp"
#include "conditions.hpp"

namespace enc
{

  void applyCondition(Combatant &combatant, const Condition &condition)
  {
    combatant.addCondition(condition);
    if(containsCondition(condition.conditions, Conditions::SWALLOWED))
      {
        combatant.setSwallower(const_cast<Combatant *>(condition.initiator));
      }
  }

  std::optional<size_t> findConditionIndex(const std::vector<Condition> &conditionList, Conditions condition, const Combatant *initiator = nullptr)
  {
    for(size_t i = 0; i < conditionList.size(); ++i)
      {
        if((!initiator || conditionList[i].initiator == initiator) && containsCondition(conditionList[i].conditions, condition))
          {
            return i;
          }
      }
    return std::nullopt;
  }

  std::optional<Condition> removeCondition(Combatant &combatant, Conditions condition, const Combatant *initiator = nullptr)
  {
    auto &conditions = combatant.getConditions();
    auto index = findConditionIndex(conditions, condition, initiator);
    if(index)
      {
        auto removedCondition = conditions[*index];
        combatant.removeCondition(condition, initiator);
        if(condition == Conditions::SWALLOWED)
          {
            combatant.setSwallower(nullptr);
          }
        return removedCondition;
      }
    return std::nullopt;
  }

  void removeAllConditionsOfType(Combatant &combatant, Conditions condition)
  {
    combatant.removeDCCondition(condition);
    combatant.removeCondition(condition);
    if(condition == Conditions::SWALLOWED)
      {
        combatant.setSwallower(nullptr);
      }
  }

  bool isAffectedBy(const Combatant &combatant, Conditions condition)
  {
    return std::any_of(combatant._dcConditions.begin(), combatant._dcConditions.end(),
                       [condition](const ConditionWithDC &cond) { return containsCondition(cond.conditions, condition); })
           || std::any_of(combatant._conditions.begin(), combatant._conditions.end(),
                          [condition](const Condition &cond) { return containsCondition(cond.conditions, condition); });
  }

  const Combatant *getGrappler(const Combatant &combatant)
  {
    for(const auto &condList : {combatant._dcConditions, combatant._conditions})
      {
        for(const auto &cond : condList)
          {
            if(containsCondition(cond.conditions, Conditions::GRAPPLED))
              {
                return cond.initiator;
              }
          }
      }
    return nullptr;
  }

  const Combatant *getSourceOfFrightened(const Combatant &combatant)
  {
    for(const auto &condList : {combatant._dcConditions, combatant._conditions})
      {
        for(const auto &cond : condList)
          {
            if(containsCondition(cond.conditions, Conditions::FRIGHTENED))
              {
                return cond.initiator;
              }
          }
      }
    return nullptr;
  }

  const Combatant *getSourceOfParalyzed(const Combatant &combatant)
  {
    for(const auto &condList : {combatant._dcConditions, combatant._conditions})
      {
        for(const auto &cond : condList)
          {
            if(containsCondition(cond.conditions, Conditions::PARALYZED))
              {
                return cond.initiator;
              }
          }
      }
    return nullptr;
  }

  const Combatant *getGrappled(const Combatant &combatant)
  {
    for(const auto &condList : {combatant._dcConditions, combatant._conditions})
      {
        for(const auto &cond : condList)
          {
            if(containsCondition(cond.conditions, Conditions::GRAPPLING))
              {
                return cond.target.value_or(nullptr);
              }
          }
      }
    return nullptr;
  }

  std::optional<ConditionWithDC> needsToBreakOutOfGrapple(const Combatant &combatant)
  {
    for(const auto &dcCond : combatant._dcConditions)
      {
        if(containsCondition(dcCond.conditions, Conditions::GRAPPLED) && dcCond.phase == PhaseOfTurn::ACTION)
          {
            return dcCond;
          }
      }
    return std::nullopt;
  }

  void breakOutOfGrapple(Combatant &combatant)
  {
    auto it = std::find_if(combatant._dcConditions.begin(), combatant._dcConditions.end(), [](const ConditionWithDC &cond) {
      return containsCondition(cond.conditions, Conditions::GRAPPLED) && cond.phase == PhaseOfTurn::ACTION;
    });
    if(it != combatant._dcConditions.end())
      {
        combatant._dcConditions.erase(it);
      }
  }

  bool isAffectedByAny(const Combatant &combatant, const std::vector<Conditions> &conditions)
  {
    for(const auto &condition : conditions)
      {
        if(isAffectedBy(combatant, condition))
          {
            return true;
          }
      }
    return false;
  }

  void applyDCCondition(Combatant &combatant, const ConditionWithDC &condition)
  {
    combatant.addDCCondition(condition);
    if(containsCondition(condition.conditions, Conditions::SWALLOWED))
      {
        combatant.setSwallower(const_cast<Combatant *>(condition.initiator));
      }
  }

  std::optional<ConditionWithDC> removeDCCondition(Combatant &combatant, Conditions condition, const Combatant *initiator = nullptr)
  {
    auto &dcConditions = combatant.getDCConditions();
    auto index = findConditionIndex(dcConditions, condition, initiator);
    if(index)
      {
        auto removedCondition = dcConditions[*index];
        combatant.removeDCCondition(condition, initiator);
        if(condition == Conditions::SWALLOWED)
          {
            combatant.setSwallower(nullptr);
          }
        return removedCondition;
      }
    return std::nullopt;
  }
}