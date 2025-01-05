#include <gtest/gtest.h>
#include "core/state_machine.hpp" // Assume this is the header for our StateMachine class
#include "actoid_for_test.hpp"

using namespace enc;

namespace
{

  class StateMachineTest : public ::testing::Test
  {
  protected:
    StateMachine fsm;
    TestActoidFactory factory;

    std::shared_ptr<Actoid> createTestAction(const std::string &name) { return factory.createTestActoid(name); }
  };

  TEST_F(StateMachineTest, BasicFunctionality)
  {
    ASSERT_EQ(fsm.getCurrentState(), INITIAL_STATE);

    fsm.addNewState(2);
    fsm.addNewState(3);
    fsm.addNewState(4);
    fsm.addNewState(5);

    auto to_2 = createTestAction("to_2");
    auto to_3 = createTestAction("to_3");
    auto to_4 = createTestAction("to_4");
    auto to_5 = createTestAction("to_5");
    auto to_terminal = createTestAction("to_terminal");

    fsm.addTransition(to_2, INITIAL_STATE, 2);
    fsm.addTransition(to_3, 2, 3);
    fsm.addTransition(to_4, 3, 4);
    fsm.addTransition(to_5, 3, 5);
    fsm.addTransition(to_terminal, 4, TERMINAL_STATE);
    fsm.addTransition(to_terminal, 5, TERMINAL_STATE);

    auto transitions = fsm.getCurrentForwardTransitions();
    ASSERT_EQ(transitions.size(), 1);
    ASSERT_EQ(transitions[0].first->toString(), "to_2");
    ASSERT_EQ(transitions[0].second, 2);

    fsm.triggerTransition(to_2);
    ASSERT_EQ(fsm.getCurrentState(), 2);

    transitions = fsm.getCurrentForwardTransitions();
    ASSERT_EQ(transitions.size(), 1);
    ASSERT_EQ(transitions[0].first->toString(), "to_3");
    ASSERT_EQ(transitions[0].second, 3);
  }

  TEST_F(StateMachineTest, RemoveTransition)
  {
    fsm.addNewState(2);
    auto to_2 = createTestAction("to_2");
    auto to_terminal = createTestAction("to_terminal");

    fsm.addTransition(to_2, INITIAL_STATE, 2);
    fsm.addTransition(to_terminal, 2, TERMINAL_STATE);

    ASSERT_NO_THROW({
      fsm.removeTransition(to_2, INITIAL_STATE);
      fsm.addTransition(to_2, INITIAL_STATE, 2);
      fsm.removeTransition(to_2, INITIAL_STATE);
      fsm.addTransition(to_2, INITIAL_STATE, 2);
    });

    auto transitions = fsm.getForwardTransitions(INITIAL_STATE);
    ASSERT_EQ(transitions.size(), 1);
    ASSERT_EQ(transitions[0].first, to_2);
  }

  TEST_F(StateMachineTest, GetNextStateId)
  {
    int id1 = fsm.getNextStateId();
    int id2 = fsm.getNextStateId();
    ASSERT_NE(id1, id2);
    ASSERT_LT(id1, id2);
  }

  TEST_F(StateMachineTest, AddExistingState)
  {
    fsm.addNewState(2);
    ASSERT_THROW(fsm.addNewState(2), std::runtime_error);
  }

  TEST_F(StateMachineTest, TriggerNonexistentTransition)
  {
    auto nonexistent = createTestAction("nonexistent");
    ASSERT_FALSE(fsm.triggerTransition(nonexistent));
  }

  TEST_F(StateMachineTest, ResetState)
  {
    fsm.addNewState(2);
    auto to_2 = createTestAction("to_2");
    fsm.addTransition(to_2, INITIAL_STATE, 2);
    fsm.triggerTransition(to_2);
    ASSERT_EQ(fsm.getCurrentState(), 2);
    fsm.reset();
    ASSERT_EQ(fsm.getCurrentState(), INITIAL_STATE);
  }

  TEST_F(StateMachineTest, GetAllStates)
  {
    fsm.addNewState(2);
    fsm.addNewState(3);
    auto to_2 = createTestAction("to_2");
    auto to_3 = createTestAction("to_3");
    auto to_terminal = createTestAction("to_terminal");

    fsm.addTransition(to_2, INITIAL_STATE, 2);
    fsm.addTransition(to_3, 2, 3);
    fsm.addTransition(to_terminal, 3, TERMINAL_STATE);

    auto states = fsm.getAllStates();
    ASSERT_EQ(states.size(), 4); // INITIAL_STATE, TERMINAL_STATE, 2, 3
    ASSERT_TRUE(std::find(states.begin(), states.end(), INITIAL_STATE) != states.end());
    ASSERT_TRUE(std::find(states.begin(), states.end(), TERMINAL_STATE) != states.end());
    ASSERT_TRUE(std::find(states.begin(), states.end(), 2) != states.end());
    ASSERT_TRUE(std::find(states.begin(), states.end(), 3) != states.end());
  }

  TEST_F(StateMachineTest, BasicToposort)
  {
    fsm.addNewState(2);
    fsm.addNewState(3);
    fsm.addNewState(4);
    fsm.addNewState(5);

    auto to_2 = createTestAction("to_2");
    auto to_3 = createTestAction("to_3");
    auto to_4 = createTestAction("to_4");
    auto to_5 = createTestAction("to_5");
    auto to_terminal = createTestAction("to_terminal");

    fsm.addTransition(to_2, INITIAL_STATE, 2);
    fsm.addTransition(to_3, 2, 3);
    fsm.addTransition(to_4, 3, 4);
    fsm.addTransition(to_5, 2, 5);
    fsm.addTransition(to_terminal, 5, TERMINAL_STATE);

    auto sorted = fsm.toposort();
    auto find_pos = [&sorted](StateId id) { return std::find(sorted.begin(), sorted.end(), id) - sorted.begin(); };

    ASSERT_EQ(sorted.size(), 6);
    ASSERT_LT(find_pos(INITIAL_STATE), find_pos(2));
    ASSERT_LT(find_pos(2), find_pos(3));
    ASSERT_LT(find_pos(2), find_pos(5));
    ASSERT_LT(find_pos(3), find_pos(4));
    ASSERT_LT(find_pos(5), find_pos(TERMINAL_STATE));
  }

  TEST_F(StateMachineTest, ToposortWithCycle)
  {
    fsm.addNewState(2);
    fsm.addNewState(3);
    fsm.addNewState(4);

    auto to_2 = createTestAction("to_2");
    auto to_3 = createTestAction("to_3");
    auto to_4 = createTestAction("to_4");
    auto cycle = createTestAction("cycle");

    fsm.addTransition(to_2, INITIAL_STATE, 2);
    fsm.addTransition(to_3, 2, 3);
    fsm.addTransition(to_4, 3, 4);
    fsm.addTransition(cycle, 4, 2);

    ASSERT_THROW(fsm.toposort(), std::runtime_error);
  }

  TEST_F(StateMachineTest, ToposortEmptyGraph)
  {
    auto sorted = fsm.toposort();
    ASSERT_EQ(sorted.size(), 2);
    ASSERT_TRUE(std::find(sorted.begin(), sorted.end(), 0) != sorted.end());
    ASSERT_TRUE(std::find(sorted.begin(), sorted.end(), TERMINAL_STATE) != sorted.end());
  }

  // TEST_F(StateMachineTest, ToposortAfterStateRemoval)
  // {
  //   fsm.addNewState(2);
  //   fsm.addNewState(3);
  //   fsm.addNewState(4);

  //   auto from_initial_to_2 = createTestAction("from_initial_to_2");
  //   auto from_2_to_3 = createTestAction("from_2_to_3");
  //   auto from_2_to_4 = createTestAction("from_2_to_4");
  //   auto from_3_to_4 = createTestAction("from_3_to_4");
  //   auto from_4_to_terminal = createTestAction("from_4_to_terminal");

  //   fsm.addTransition(from_initial_to_2, INITIAL_STATE, 2);
  //   fsm.addTransition(from_2_to_3, 2, 3);
  //   fsm.addTransition(from_2_to_4, 2, 4);
  //   fsm.addTransition(from_3_to_4, 3, 4);
  //   fsm.addTransition(from_4_to_terminal, 4, TERMINAL_STATE);

  //   auto sorted = fsm.toposort();
  //   ASSERT_EQ(sorted.size(), 5);
  //   auto find_pos = [&sorted](StateId id) { return std::find(sorted.begin(), sorted.end(), id) - sorted.begin(); };

  //   ASSERT_LT(find_pos(INITIAL_STATE), find_pos(2));
  //   ASSERT_LT(find_pos(INITIAL_STATE), find_pos(3));
  //   ASSERT_LT(find_pos(2), find_pos(3));
  //   ASSERT_LT(find_pos(INITIAL_STATE), find_pos(4));
  //   ASSERT_LT(find_pos(2), find_pos(4));
  //   ASSERT_LT(find_pos(3), find_pos(4));
  //   ASSERT_LT(find_pos(INITIAL_STATE), find_pos(TERMINAL_STATE));
  //   ASSERT_LT(find_pos(2), find_pos(TERMINAL_STATE));
  //   ASSERT_LT(find_pos(3), find_pos(TERMINAL_STATE));
  //   ASSERT_LT(find_pos(4), find_pos(TERMINAL_STATE));

  //   fsm.removeState(3);
  //   sorted = fsm.toposort();

  //   ASSERT_EQ(sorted.size(), 4);

  //   ASSERT_LT(find_pos(INITIAL_STATE), find_pos(2));
  //   ASSERT_LT(find_pos(INITIAL_STATE), find_pos(4));
  //   ASSERT_LT(find_pos(2), find_pos(4));
  //   ASSERT_LT(find_pos(INITIAL_STATE), find_pos(TERMINAL_STATE));
  //   ASSERT_LT(find_pos(2), find_pos(TERMINAL_STATE));
  //   ASSERT_LT(find_pos(4), find_pos(TERMINAL_STATE));
  //   ASSERT_TRUE(std::find(sorted.begin(), sorted.end(), 3) == sorted.end());
  // }

  TEST_F(StateMachineTest, ToposortMultiplePathsToSameNode)
  {
    fsm.addNewState(2);
    fsm.addNewState(3);
    fsm.addNewState(4);

    auto to_2 = createTestAction("to_2");
    auto to_3 = createTestAction("to_3");
    auto to_4_from_2 = createTestAction("to_4_from_2");
    auto to_4_from_3 = createTestAction("to_4_from_3");

    fsm.addTransition(to_2, INITIAL_STATE, 2);
    fsm.addTransition(to_3, INITIAL_STATE, 3);
    fsm.addTransition(to_4_from_2, 2, 4);
    fsm.addTransition(to_4_from_3, 3, 4);

    auto sorted = fsm.toposort();
    ASSERT_EQ(sorted.size(), 5);

    auto find_pos = [&sorted](StateId id) { return std::find(sorted.begin(), sorted.end(), id) - sorted.begin(); };

    ASSERT_LT(find_pos(0), find_pos(2));
    ASSERT_LT(find_pos(0), find_pos(3));
    ASSERT_LT(find_pos(2), find_pos(4));
    ASSERT_LT(find_pos(3), find_pos(4));
  }

  int main(int argc, char **argv)
  {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
  }

}
