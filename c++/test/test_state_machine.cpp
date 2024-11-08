#include <gtest/gtest.h>
#include "core/state_machine.hpp" // Assume this is the header for our StateMachine class

using namespace enc;

namespace {

class StateMachineTest : public ::testing::Test {
protected:
    StateMachine fsm;
};

TEST_F(StateMachineTest, BasicFunctionality) {
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

    ASSERT_EQ(fsm.getAvailableTransitionsInCurrentState(), std::vector<std::string>{"to_2"});

    fsm.triggerTransition("to_2");
    ASSERT_EQ(fsm.getCurrentState(), 2);
    ASSERT_EQ(fsm.getAvailableTransitionsInCurrentState(), std::vector<std::string>{"to_3"});

    fsm.triggerTransition("to_3");
    ASSERT_EQ(fsm.getCurrentState(), 3);
    ASSERT_EQ(fsm.getAvailableTransitionsInCurrentState(), (std::vector<std::string>{"to_4", "to_5"}));

    fsm.triggerTransition("to_4");
    ASSERT_EQ(fsm.getCurrentState(), 4);
    ASSERT_EQ(fsm.getAvailableTransitionsInCurrentState(), std::vector<std::string>{"to_-1"});

    fsm.triggerTransition("to_-1");
    ASSERT_EQ(fsm.getCurrentState(), -1);
    ASSERT_TRUE(fsm.getAvailableTransitionsInCurrentState().empty());
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
    auto transitions = fsm.getAvailableTransitionsInState(0);
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
    ASSERT_THROW(fsm.triggerTransition("nonexistent"), std::runtime_error);
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

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}

}
