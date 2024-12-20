#include <gtest/gtest.h>
#include "core/state_machine.hpp" // Assume this is the header for our StateMachine class

using namespace enc;

namespace {

class StateMachineTest : public ::testing::Test {
protected:
    StateMachine fsm;
};

// TEST_F(StateMachineTest, BasicFunctionality) {
//     ASSERT_EQ(fsm.getCurrentState(), 0);

//     fsm.addNewState(2);
//     fsm.addNewState(3);
//     fsm.addNewState(4);
//     fsm.addNewState(5);

//     fsm.addTransition("to_2", 0, 2);
//     fsm.addTransition("to_3", 2, 3);
//     fsm.addTransition("to_4", 3, 4);
//     fsm.addTransition("to_5", 3, 5);
//     fsm.addTransition("to_-1", 4, -1);
//     fsm.addTransition("to_-1", 5, -1);

//     ASSERT_EQ(fsm.getAvailableTransitionsInCurrentState(), std::vector<std::string>{"to_2"});

//     fsm.triggerTransition("to_2");
//     ASSERT_EQ(fsm.getCurrentState(), 2);
//     ASSERT_EQ(fsm.getAvailableTransitionsInCurrentState(), std::vector<std::string>{"to_3"});

//     fsm.triggerTransition("to_3");
//     ASSERT_EQ(fsm.getCurrentState(), 3);
//     ASSERT_EQ(fsm.getAvailableTransitionsInCurrentState(), (std::vector<std::string>{"to_4", "to_5"}));

//     fsm.triggerTransition("to_4");
//     ASSERT_EQ(fsm.getCurrentState(), 4);
//     ASSERT_EQ(fsm.getAvailableTransitionsInCurrentState(), std::vector<std::string>{"to_-1"});

//     fsm.triggerTransition("to_-1");
//     ASSERT_EQ(fsm.getCurrentState(), -1);
//     ASSERT_TRUE(fsm.getAvailableTransitionsInCurrentState().empty());
// }

TEST_F(StateMachineTest, BasicFunctionality)
{
  ASSERT_EQ(fsm.getCurrentState(), 0);

  fsm.addNewState(2);
  fsm.addNewState(3);
  fsm.addNewState(4);
  fsm.addNewState(5);

  fsm.addTransition("to_2", 0, 2);
  fsm.addTransition("to_3", 2, 3);
  fsm.addTransition("to_4", 3, 4);
  fsm.addTransition("to_5", 3, 5);
  fsm.addTransition("to_-1", 4, -1);
  fsm.addTransition("to_-1", 5, -1);

  // Instead of checking just transition names, we check the full transitions
  auto transitions = fsm.getForwardTransitions(fsm.getCurrentState());
  ASSERT_EQ(transitions.size(), 1);
  ASSERT_EQ(transitions[0].first, "to_2");
  ASSERT_EQ(transitions[0].second, 2);

  fsm.triggerTransition("to_2");
  ASSERT_EQ(fsm.getCurrentState(), 2);

  transitions = fsm.getForwardTransitions(fsm.getCurrentState());
  ASSERT_EQ(transitions.size(), 1);
  ASSERT_EQ(transitions[0].first, "to_3");
  ASSERT_EQ(transitions[0].second, 3);

  fsm.triggerTransition("to_3");
  ASSERT_EQ(fsm.getCurrentState(), 3);

  transitions = fsm.getForwardTransitions(fsm.getCurrentState());
  ASSERT_EQ(transitions.size(), 2);
  // Sort transitions to make test deterministic
  std::sort(transitions.begin(), transitions.end());
  ASSERT_EQ(transitions[0].first, "to_4");
  ASSERT_EQ(transitions[0].second, 4);
  ASSERT_EQ(transitions[1].first, "to_5");
  ASSERT_EQ(transitions[1].second, 5);

  fsm.triggerTransition("to_4");
  ASSERT_EQ(fsm.getCurrentState(), 4);

  transitions = fsm.getForwardTransitions(fsm.getCurrentState());
  ASSERT_EQ(transitions.size(), 1);
  ASSERT_EQ(transitions[0].first, "to_-1");
  ASSERT_EQ(transitions[0].second, -1);

  fsm.triggerTransition("to_-1");
  ASSERT_EQ(fsm.getCurrentState(), -1);
  ASSERT_TRUE(fsm.getForwardTransitions(fsm.getCurrentState()).empty());
}

TEST_F(StateMachineTest, RemoveStateAndTransition) {
    fsm.addNewState(2); // A
    fsm.addTransition("to_1", 0, 2);
    fsm.addTransition("to_-1", 2, -1);

    ASSERT_NO_THROW({
        fsm.removeTransition("to_1", 0);
        fsm.addTransition("to_1", 0, 2);
        fsm.removeTransition("to_1", 0);
        fsm.addTransition("to_1", 0, 2);
    });

    // Test removing a state
    ASSERT_NO_THROW({
        fsm.removeState(2);
    });

    // Verify that transitions to the removed state are also removed
    auto transitions = fsm.getForwardTransitions(0);
    ASSERT_TRUE(std::find(transitions.begin(), transitions.end(), "to_1") == transitions.end());
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
    ASSERT_FALSE(fsm.triggerTransition("nonexistent"));
}

TEST_F(StateMachineTest, ResetState) {
    fsm.addNewState(2);
    fsm.addTransition("to_2", 0, 2);
    fsm.triggerTransition("to_2");
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

  fsm.addTransition("to_2", 0, 2);
  fsm.addTransition("to_3", 2, 3);
  fsm.addTransition("to_4", 3, 4);
  fsm.addTransition("to_5", 2, 5);

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

  fsm.addTransition("to_2", 0, 2);
  fsm.addTransition("to_3", 2, 3);
  fsm.addTransition("to_4", 3, 4);
  fsm.addTransition("cycle", 4, 2); // Creates cycle

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

  fsm.addTransition("to_2", 0, 2);
  fsm.addTransition("to_3", 2, 3);
  fsm.addTransition("to_4", 3, 4);

  auto sorted = fsm.toposort();

  ASSERT_EQ(sorted.size(), 5); // 0, -1, 2, 3, 4

  // Remove middle state
  fsm.removeState(3);

  sorted = fsm.toposort();

  // Check size
  ASSERT_EQ(sorted.size(), 4); // 0, -1, 2, 4

  // Verify 2 and 4 are no longer connected in ordering
  auto find_pos = [&sorted](StateId id) { return std::find(sorted.begin(), sorted.end(), id) - sorted.begin(); };

  ASSERT_LT(find_pos(0), find_pos(2));
  ASSERT_LT(find_pos(2), find_pos(4));
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

  fsm.addTransition("to_2", 0, 2);
  fsm.addTransition("to_3", 0, 3);
  fsm.addTransition("to_4_from_2", 2, 4);
  fsm.addTransition("to_4_from_3", 3, 4);

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
