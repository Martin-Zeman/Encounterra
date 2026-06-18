#include <gtest/gtest.h>
#include <algorithm>
#include <memory>
#include <string>
#include <vector>
#include "core/state_machine.hpp"
#include "actions/dummy_actoid.hpp"
#include "actions/dummy_actoid_factory.hpp"

using namespace enc;

namespace {

class StateMachineTest : public ::testing::Test {
protected:
    StateMachine fsm;
    // Keeps the synthetic transition actoids alive for the lifetime of the test; the StateMachine stores raw
    // non-owning Actoid* and matches transitions by pointer identity.
    std::vector<std::shared_ptr<Actoid>> actoidPool;

    Actoid *makeActoid(const std::string &name)
    {
        auto actoid = std::make_shared<DummyActoid>(DummyActoidFactory::getInstance(), name);
        Actoid *raw = actoid.get();
        actoidPool.push_back(std::move(actoid));
        return raw;
    }
};

TEST_F(StateMachineTest, BasicFunctionality)
{
  ASSERT_EQ(fsm.getCurrentState(), 0);

  fsm.addNewState(2);
  fsm.addNewState(3);
  fsm.addNewState(4);
  fsm.addNewState(5);

  Actoid *to_2 = makeActoid("to_2");
  Actoid *to_3 = makeActoid("to_3");
  Actoid *to_4 = makeActoid("to_4");
  Actoid *to_5 = makeActoid("to_5");
  Actoid *to_neg1_from_4 = makeActoid("to_-1");
  Actoid *to_neg1_from_5 = makeActoid("to_-1");

  fsm.addTransition(to_2, 0, 2);
  fsm.addTransition(to_3, 2, 3);
  fsm.addTransition(to_4, 3, 4);
  fsm.addTransition(to_5, 3, 5);
  fsm.addTransition(to_neg1_from_4, 4, -1);
  fsm.addTransition(to_neg1_from_5, 5, -1);

  // Check the full transitions (action identity + destination)
  auto transitions = fsm.getCurrentForwardTransitions();
  ASSERT_EQ(transitions.size(), 1);
  ASSERT_EQ(transitions[0].first, to_2);
  ASSERT_EQ(transitions[0].second, 2);

  fsm.triggerTransition(to_2);
  ASSERT_EQ(fsm.getCurrentState(), 2);

  transitions = fsm.getCurrentForwardTransitions();
  ASSERT_EQ(transitions.size(), 1);
  ASSERT_EQ(transitions[0].first, to_3);
  ASSERT_EQ(transitions[0].second, 3);

  fsm.triggerTransition(to_3);
  ASSERT_EQ(fsm.getCurrentState(), 3);

  transitions = fsm.getCurrentForwardTransitions();
  ASSERT_EQ(transitions.size(), 2);
  // Sort transitions by destination to make the test deterministic
  std::sort(transitions.begin(), transitions.end(),
            [](const auto &a, const auto &b) { return a.second < b.second; });
  ASSERT_EQ(transitions[0].first, to_4);
  ASSERT_EQ(transitions[0].second, 4);
  ASSERT_EQ(transitions[1].first, to_5);
  ASSERT_EQ(transitions[1].second, 5);

  fsm.triggerTransition(to_4);
  ASSERT_EQ(fsm.getCurrentState(), 4);

  transitions = fsm.getCurrentForwardTransitions();
  ASSERT_EQ(transitions.size(), 1);
  ASSERT_EQ(transitions[0].first, to_neg1_from_4);
  ASSERT_EQ(transitions[0].second, -1);

  fsm.triggerTransition(to_neg1_from_4);
  ASSERT_EQ(fsm.getCurrentState(), -1);
  ASSERT_TRUE(fsm.getCurrentForwardTransitions().empty());
}

TEST_F(StateMachineTest, RemoveStateAndTransition) {
    fsm.addNewState(2); // A
    Actoid *to_1 = makeActoid("to_1");
    Actoid *to_neg1 = makeActoid("to_-1");
    fsm.addTransition(to_1, 0, 2);
    fsm.addTransition(to_neg1, 2, -1);

    ASSERT_NO_THROW({
        fsm.removeTransition(to_1, 0);
        fsm.addTransition(to_1, 0, 2);
        fsm.removeTransition(to_1, 0);
        fsm.addTransition(to_1, 0, 2);
    });

    // Test removing a state
    ASSERT_NO_THROW({
        fsm.removeState(2);
    });

    // Verify that transitions to the removed state are also removed
    auto transitions = fsm.getForwardActoidTransitions(0);
    ASSERT_TRUE(std::none_of(transitions.begin(), transitions.end(),
                             [&](const std::pair<Actoid *, StateId> &t) { return t.first == to_1; }));
}

TEST_F(StateMachineTest, GetNextStateId) {
    int id1 = fsm.getNextStateId();
    int id2 = fsm.getNextStateId();
    ASSERT_NE(id1, id2);
    ASSERT_LT(id1, id2);
}

TEST_F(StateMachineTest, AddExistingState) {
    fsm.addNewState(2);
    ASSERT_THROW(fsm.addNewState(2), std::runtime_error);
}

TEST_F(StateMachineTest, TriggerNonexistentTransition) {
    Actoid *unknown = makeActoid("nonexistent");
    ASSERT_FALSE(fsm.triggerTransition(unknown));
}

TEST_F(StateMachineTest, ResetState) {
    fsm.addNewState(2);
    Actoid *to_2 = makeActoid("to_2");
    fsm.addTransition(to_2, 0, 2);
    fsm.triggerTransition(to_2);
    ASSERT_EQ(fsm.getCurrentState(), 2);
    fsm.reset();
    ASSERT_EQ(fsm.getCurrentState(), 0);
}

TEST_F(StateMachineTest, GetAllStates) {
    fsm.addNewState(2);
    fsm.addNewState(3);
    auto states = fsm.getAllStates();
    ASSERT_EQ(states.size(), 4); // 0, -1, 2, 3
    ASSERT_TRUE(std::find(states.begin(), states.end(), 0) != states.end());
    ASSERT_TRUE(std::find(states.begin(), states.end(), -1) != states.end());
    ASSERT_TRUE(std::find(states.begin(), states.end(), 2) != states.end());
    ASSERT_TRUE(std::find(states.begin(), states.end(), 3) != states.end());
}

TEST_F(StateMachineTest, BasicToposort)
{
  // Create a simple DAG:
  // 0 -> 2 -> 3 -> 4
  //        \-> 5
  fsm.addNewState(2);
  fsm.addNewState(3);
  fsm.addNewState(4);
  fsm.addNewState(5);

  fsm.addTransition(makeActoid("to_2"), 0, 2);
  fsm.addTransition(makeActoid("to_3"), 2, 3);
  fsm.addTransition(makeActoid("to_4"), 3, 4);
  fsm.addTransition(makeActoid("to_5"), 2, 5);

  auto sorted = fsm.toposort();

  auto find_pos = [&sorted](StateId id) { return std::find(sorted.begin(), sorted.end(), id) - sorted.begin(); };

  ASSERT_EQ(sorted.size(), 6); // 0, -1, 2, 3, 4, 5

  ASSERT_LT(find_pos(0), find_pos(2)); // 0 before 2
  ASSERT_LT(find_pos(2), find_pos(3)); // 2 before 3
  ASSERT_LT(find_pos(2), find_pos(5)); // 2 before 5
  ASSERT_LT(find_pos(3), find_pos(4)); // 3 before 4
}

TEST_F(StateMachineTest, ToposortWithCycle)
{
  // Create a graph with a cycle:
  // 0 -> 2 -> 3 -> 4
  //      ^         |
  //      |---------|
  fsm.addNewState(2);
  fsm.addNewState(3);
  fsm.addNewState(4);

  fsm.addTransition(makeActoid("to_2"), 0, 2);
  fsm.addTransition(makeActoid("to_3"), 2, 3);
  fsm.addTransition(makeActoid("to_4"), 3, 4);
  fsm.addTransition(makeActoid("cycle"), 4, 2); // Creates cycle

  ASSERT_THROW(fsm.toposort(), std::runtime_error);
}

TEST_F(StateMachineTest, ToposortEmptyGraph)
{
  // The graph starts with states 0 and -1
  auto sorted = fsm.toposort();
  ASSERT_EQ(sorted.size(), 2);
  // Check that initial and NOP states are present
  ASSERT_TRUE(std::find(sorted.begin(), sorted.end(), 0) != sorted.end());
  ASSERT_TRUE(std::find(sorted.begin(), sorted.end(), -1) != sorted.end());
}

TEST_F(StateMachineTest, ToposortAfterStateRemoval)
{
  // Initial setup
  fsm.addNewState(2);
  fsm.addNewState(3);
  fsm.addNewState(4);

  fsm.addTransition(makeActoid("to_2"), 0, 2);
  fsm.addTransition(makeActoid("to_3"), 2, 3);
  fsm.addTransition(makeActoid("to_4"), 3, 4);

  auto sorted = fsm.toposort();

  ASSERT_EQ(sorted.size(), 5); // 0, -1, 2, 3, 4

  // Remove middle state
  fsm.removeState(3);

  sorted = fsm.toposort();

  // Check size
  ASSERT_EQ(sorted.size(), 4); // 0, -1, 2, 4

  // After removing the middle state, the chain 0 -> 2 -> 3 -> 4 leaves only the
  // edge 0 -> 2 (the 2 -> 3 and 3 -> 4 edges are gone with state 3). State 4 is
  // now disconnected, so its position relative to 2 is unconstrained.
  auto find_pos = [&sorted](StateId id) { return std::find(sorted.begin(), sorted.end(), id) - sorted.begin(); };

  ASSERT_LT(find_pos(0), find_pos(2)); // surviving edge 0 -> 2 preserved
  ASSERT_TRUE(std::find(sorted.begin(), sorted.end(), 2) != sorted.end()); // 2 is present
  ASSERT_TRUE(std::find(sorted.begin(), sorted.end(), 4) != sorted.end()); // 4 is present (disconnected)
  ASSERT_TRUE(std::find(sorted.begin(), sorted.end(), 3) == sorted.end()); // 3 is gone
}

TEST_F(StateMachineTest, ToposortMultiplePathsToSameNode)
{
  // Create a diamond pattern:
  //    0
  //  /   \
  // 2     3
  //  \   /
  //    4
  fsm.addNewState(2);
  fsm.addNewState(3);
  fsm.addNewState(4);

  fsm.addTransition(makeActoid("to_2"), 0, 2);
  fsm.addTransition(makeActoid("to_3"), 0, 3);
  fsm.addTransition(makeActoid("to_4_from_2"), 2, 4);
  fsm.addTransition(makeActoid("to_4_from_3"), 3, 4);

  auto sorted = fsm.toposort();

  // Verify basic properties
  ASSERT_EQ(sorted.size(), 5); // 0, -1, 2, 3, 4

  auto find_pos = [&sorted](StateId id) { return std::find(sorted.begin(), sorted.end(), id) - sorted.begin(); };

  // Verify topological ordering constraints
  ASSERT_LT(find_pos(0), find_pos(2));
  ASSERT_LT(find_pos(0), find_pos(3));
  ASSERT_LT(find_pos(2), find_pos(4));
  ASSERT_LT(find_pos(3), find_pos(4));
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}

}
