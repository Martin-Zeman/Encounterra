#include "actions/action_protodag.hpp"

#include <any>
#include <functional>
#include <optional>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>

#include "actions/action_types.hpp"
#include "actions/action_selection.hpp"
#include "core/combatant.hpp"
#include "core/resources.hpp"
#include "effects/action_enabler_effect.hpp"

namespace enc
{
  namespace
  {
    /**
     * Factory-level light feasibility check. This is the faithful port of Python's check_feasibility_light(), which
     * operates on (action_type, factory) tuples (i.e. before any action is instantiated). The C++ Actoid-based
     * checkFeasibilityLight() is the same predicate, just expressed over an already-created Actoid.
     */
    bool isFactoryFeasibleLight(Combatant *combatant, ActoidFactory *factory)
    {
      const AbilityType abilityType = factory->getAbilityType();
      bool result;
      if(abilityType > AbilityType::NOP && abilityType < AbilityType::BONUS_ACTION_DELIMITER)
        result = combatant->hasAction();
      else if(abilityType > AbilityType::BONUS_ACTION_DELIMITER && abilityType < AbilityType::REACTION_DELIMITER)
        result = combatant->hasBonusAction();
      else if(abilityType > AbilityType::HASTE_ACTION_DELIMITER && abilityType < AbilityType::PASSIVE_DELIMITER)
        result = combatant->hasHasteAction();
      else
        return false;

      switch(abilityType)
        {
        case AbilityType::MELEE_ATTACK:
        case AbilityType::RANGED_ATTACK:
        case AbilityType::HASTE_MELEE_ATTACK:
        case AbilityType::HASTE_RANGED_ATTACK:
        case AbilityType::VAMPIRIC_BITE:
        case AbilityType::HASTE_VAMPIRIC_BITE:
        case AbilityType::PARALYZING_MELEE_ATTACK:
        case AbilityType::HASTE_PARALYZING_MELEE_ATTACK:
          {
            // Multiattack: a second, complementary attack can be granted by the attack FSM even once the action
            // economy is spent (mirrors Python feasibility's `res |= not attack_fsm.is_0() and ...`).
            result = result || (!combatant->isAttackFsmAtStart() && combatant->attackFsmHasTransition(factory));
            if(auto ammo = factory->getResource())
              result = result && (*ammo)->hasUses();
            else
              throw std::runtime_error("Attack factory has no ammo!");
            break;
          }
        case AbilityType::FIREBALL:
        case AbilityType::HUNGER_OF_HADAR:
          {
            if(auto resource = factory->getResource())
              result = result && (*resource)->hasUses(3);
            else
              throw std::runtime_error("Actoid factory must have an associated resource!");
            result = result && !combatant->hasAlreadyUsedSpellslotThisTurn();
            break;
          }
        case AbilityType::SCORCHING_RAY:
        case AbilityType::HOLD_PERSON:
        case AbilityType::MISTY_STEP:
          {
            if(auto resource = factory->getResource())
              result = result && (*resource)->hasUses(2);
            else
              throw std::runtime_error("Actoid factory must have an associated resource!");
            result = result && !combatant->hasAlreadyUsedSpellslotThisTurn();
            break;
          }
        case AbilityType::QUICKENED_SCORCHING_RAY:
        case AbilityType::QUICKENED_HOLD_PERSON:
          {
            if(auto resource = factory->getResource())
              result = result && (*resource)->hasUses(2);
            else
              throw std::runtime_error("Actoid factory must have an associated resource!");
            result = result && !combatant->hasAlreadyUsedSpellslotThisTurn();
            result = result && combatant->getSorceryPoints() > 1;
            break;
          }
        case AbilityType::TWINNED_HOLD_PERSON:
          {
            // Twinned Spell (2024): costs 1 sorcery point to add a second target.
            if(auto resource = factory->getResource())
              result = result && (*resource)->hasUses(2);
            else
              throw std::runtime_error("Actoid factory must have an associated resource!");
            result = result && !combatant->hasAlreadyUsedSpellslotThisTurn();
            result = result && combatant->getSorceryPoints() > 0;
            break;
          }
        case AbilityType::QUICKENED_FIREBOLT:
        case AbilityType::QUICKENED_RAY_OF_FROST:
          {
            result = result && combatant->getSorceryPoints() > 1;
            break;
          }
        case AbilityType::MOON_WILDSHAPE:
        case AbilityType::WILDSHAPE:
          {
            // Wild Shape is limited to a fixed number of uses per short rest (held by the factory's resource).
            // It cannot be used while already shaped (the active-form id is non-zero); the same-form filter in
            // WildshapeFactory::createAll plus this guard prevent re-shaping mid-form.
            if(auto resource = factory->getResource())
              result = result && (*resource)->hasUses();
            result = result && combatant->getActiveWildshapeFormId() == 0;
            break;
          }
        case AbilityType::HEALING_WORD:
        case AbilityType::CURE_WOUNDS:
        case AbilityType::THUNDERWAVE:
        case AbilityType::FAERIE_FIRE:
          {
            if(auto resource = factory->getResource())
              result = result && (*resource)->hasUses(1);
            else
              throw std::runtime_error("Actoid factory must have an associated resource!");
            result = result && !combatant->hasAlreadyUsedSpellslotThisTurn();
            break;
          }
        case AbilityType::SPIKE_GROWTH:
        case AbilityType::FLAMING_SPHERE:
        case AbilityType::MOONBEAM:
          {
            if(auto resource = factory->getResource())
              result = result && (*resource)->hasUses(2);
            else
              throw std::runtime_error("Actoid factory must have an associated resource!");
            result = result && !combatant->hasAlreadyUsedSpellslotThisTurn();
            break;
          }
        case AbilityType::FIREBOLT: /*Nothing to do*/ break;
        default: break;
        }
      return result;
    }

    // Builds the hashable state footprint. A state in the FSM is uniquely identified by the set of actions available
    // within it, now keyed by each action's value-based identity hash (Actoid::getHash()) instead of its string
    // representation. The optional depthMarker disambiguates two identical consecutive action sets (protection against
    // three consecutive attacks), mirroring the previous "insert std::to_string(depth)" trick.
    struct ActionFootprint
    {
      std::set<std::size_t> actionHashes;
      int depthMarker = -1; // -1 == no depth disambiguation

      bool isEmpty() const { return actionHashes.empty() && depthMarker == -1; }

      bool operator==(const ActionFootprint &other) const
      {
        return depthMarker == other.depthMarker && actionHashes == other.actionHashes;
      }
    };

    struct ActionFootprintHash
    {
      std::size_t operator()(const ActionFootprint &fp) const
      {
        std::size_t hash = std::hash<int>{}(fp.depthMarker);
        for(std::size_t ah : fp.actionHashes)
          hash ^= ah + 0x9e3779b9 + (hash << 6) + (hash >> 2);
        return hash;
      }
    };

    ActionFootprint actionsToFootprint(const std::vector<std::shared_ptr<Actoid>> &actions)
    {
      ActionFootprint footprint;
      for(const auto &action : actions)
        footprint.actionHashes.insert(action->getHash());
      return footprint;
    }
  } // namespace

  std::vector<std::shared_ptr<ActoidFactory>> getAllFeasibleActionFactories(Combatant *combatant, int depth)
  {
    std::vector<std::shared_ptr<ActoidFactory>> result;

    auto collect = [&](const std::vector<std::shared_ptr<ActoidFactory>> &factories, bool skipMistyStep) {
      for(const auto &factory : factories)
        {
          // Misty Step is excluded once we are past the first decision level - it is resolved separately as a
          // dedicated movement transition rather than a regular bonus action.
          if(skipMistyStep && factory->getAbilityType() == AbilityType::MISTY_STEP)
            continue;
          if(isFactoryFeasibleLight(combatant, factory.get()))
            result.push_back(factory);
        }
    };

    collect(combatant->getActionFactoriesConst(), false);
    collect(combatant->getBonusActionFactoriesConst(), depth > 1);
    collect(combatant->getHasteActionFactoriesConst(), false);
    return result;
  }

  ProtoDagResult generateProtoDag(Combatant *combatant)
  {
    ProtoDagResult out;
    StateMachine &fsm = out.fsm;
    ActoidOwnershipPool &actoidPool = out.actoidPool;

    using Fas = std::vector<std::shared_ptr<Actoid>>;
    using AfToA = std::unordered_map<ActoidFactory *, Fas>;

    // Hash-keyed footprint maps for the performance-critical state dedup.
    std::unordered_map<ActionFootprint, StateId, ActionFootprintHash> stateFootprintToStateName;
    std::unordered_set<ActionFootprint, ActionFootprintHash> visited;

    // The StateMachine constructor already provides the initial state (0) and the nop sink (-1).
    constexpr StateId NOP_STATE = -1;
    // Mirrors Python last_added_state='-1'; the first call returns 0 and reuses the existing initial state, then 1, 2...
    StateId lastAddedState = -1;
    auto nextStateName = [&]() { return ++lastAddedState; };

    std::function<void(Combatant *, StateId, AfToA, int, std::shared_ptr<Actoid>, std::optional<Fas>)> dfs =
      [&](Combatant *subject, StateId previousState, AfToA afToA, int depth, std::shared_ptr<Actoid> actionTaken,
          std::optional<Fas> previousFas) {
        auto fafs = getAllFeasibleActionFactories(subject, depth);

        // Build the flattened action list. Recompute afToA if it does not cover the current set of feasible factories
        // (Python recomputes on KeyError).
        bool covered = true;
        for(const auto &faf : fafs)
          if(afToA.find(faf.get()) == afToA.end())
            {
              covered = false;
              break;
            }
        if(!covered)
          {
            afToA.clear();
            for(const auto &faf : fafs)
              afToA[faf.get()] = faf->createAll();
          }

        Fas fas;
        for(const auto &faf : fafs)
          for(const auto &action : afToA[faf.get()])
            fas.push_back(action);

        // A state is defined by the set of (bonus) actions available within it. Two identical consecutive action sets
        // are distinguished by appending the depth (protection against three consecutive attacks).
        const bool sameAsPrevious = previousFas.has_value() && previousFas.value() == fas;
        ActionFootprint stateFootprint = actionsToFootprint(fas);
        if(sameAsPrevious)
          stateFootprint.depthMarker = depth;

        // The FSM transition name only feeds the flattened-DAG dedup/simplification path (indexToTransition). Build it
        // from the actoid's memoised value hash plus the depth, avoiding the expensive toString() rendering. The
        // trailing "_<depth>" keeps the simplified-name stripping (drop the depth level) working as before.
        const std::string actionTakenName =
          (actionTaken ? std::to_string(actionTaken->getHash()) : std::string("None")) + "_" + std::to_string(depth);
        if(actionTaken)
          actoidPool[actionTaken.get()] = actionTaken;

        if(stateFootprint.isEmpty())
          {
            // No more actions available -> connect to the nop sink.
            fsm.addTransition(actionTaken.get(), actionTakenName, previousState, NOP_STATE);
          }
        else if(visited.find(stateFootprint) == visited.end())
          {
            visited.insert(stateFootprint);
            const StateId currState = nextStateName();
            stateFootprintToStateName[stateFootprint] = currState;
            if(actionTaken)
              {
                fsm.addNewState(currState);
                fsm.addTransition(actionTaken.get(), actionTakenName, previousState, currState);
              }
            for(const auto &fa : fas)
              {
                std::any exportedResources = subject->exportResources();
                useResources(subject, *fa);

                auto *enabler = dynamic_cast<ActionEnablerEffect *>(fa.get());
                if(enabler)
                  {
                    // Covers action enablers in general and wildshape: Wildshape::enable() transfers the form's
                    // factories onto the subject, which unifies Python's as_if_used_action_enabler and
                    // replace_combatant_if_action_is_wildshape into a single mechanism.
                    enabler->enable();
                    auto fafsUsed = getAllFeasibleActionFactories(subject, depth);
                    AfToA afToAUsed;
                    for(const auto &faf : fafsUsed)
                      afToAUsed[faf.get()] = faf->createAll(fa.get());
                    dfs(subject, currState, afToAUsed, depth + 1, fa, fas);
                    enabler->disable();
                  }
                else if(fa->hasFlag(ActoidFlags::IS_ACTION_ENABLER))
                  {
                    AfToA afToAUsed;
                    for(const auto &faf : fafs)
                      afToAUsed[faf.get()] = faf->createAll(fa.get());
                    dfs(subject, currState, afToAUsed, depth + 1, fa, fas);
                  }
                else
                  {
                    dfs(subject, currState, afToA, depth + 1, fa, fas);
                  }

                subject->importResources(exportedResources);
              }
          }
        else
          {
            fsm.addTransition(actionTaken.get(), actionTakenName, previousState, stateFootprintToStateName[stateFootprint]);
          }
      };

    // Optimization: create_all output is stable for a given factory set, only feasibility changes => precompute root.
    auto fafs = getAllFeasibleActionFactories(combatant, 0);
    AfToA afToA;
    for(const auto &faf : fafs)
      afToA[faf.get()] = faf->createAll();

    dfs(combatant, 0, afToA, 0, nullptr, std::nullopt);

    return out;
  }
} // namespace enc
