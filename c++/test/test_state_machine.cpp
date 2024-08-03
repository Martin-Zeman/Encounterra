#include <gtest/gtest.h>
#include "core/state_machine.hpp" // Assume this is the header for our StateMachine class

using namespace enc;

class StateMachineTest : public ::testing::Test {
protected:
    StateMachine fsm;
};

TEST_F(StateMachineTest, BasicFunctionality) {
    ASSERT_EQ(fsm.get_current_state(), 0);

    fsm.add_new_state(2); // A
    fsm.add_new_state(3); // B
    fsm.add_new_state(4); // C
    fsm.add_new_state(5); // D

    fsm.add_transition("to_2", 0, 2);
    fsm.add_transition("to_3", 2, 3);
    fsm.add_transition("to_4", 3, 4);
    fsm.add_transition("to_D", 3, 5);
    fsm.add_transition("to_-1", 4, -1);
    fsm.add_transition("to_-1", 5, -1);

    ASSERT_EQ(fsm.get_available_transitions_in_current_state(), std::vector<std::string>{"to_3"});

    fsm.trigger_transition("to_2");
    ASSERT_EQ(fsm.get_current_state(), 2);
    ASSERT_EQ(fsm.get_available_transitions_in_current_state(), std::vector<std::string>{"to_3"});

    fsm.trigger_transition("to_3");
    ASSERT_EQ(fsm.get_current_state(), 3);
    ASSERT_EQ(fsm.get_available_transitions_in_current_state(), (std::vector<std::string>{"to_3", "to_4"}));

    fsm.trigger_transition("to_4");
    ASSERT_EQ(fsm.get_current_state(), 5);
    ASSERT_EQ(fsm.get_available_transitions_in_current_state(), std::vector<std::string>{"to_-1"});

    fsm.trigger_transition("to_-1");
    ASSERT_EQ(fsm.get_current_state(), 1);
    ASSERT_TRUE(fsm.get_available_transitions_in_current_state().empty());
}

TEST_F(StateMachineTest, RemoveStateAndTransition) {
    fsm.add_new_state(2); // A
    fsm.add_transition("to_1", 0, 2);
    fsm.add_transition("to_-1", 2, -1);

    ASSERT_NO_THROW({
        fsm.remove_transition("to_1", 0);
        fsm.add_transition("to_1", 0, 2);
        fsm.remove_transition("to_1", 0);
        fsm.add_transition("to_1", 0, 2);
    });

    // Test removing a state
    ASSERT_NO_THROW({
        fsm.remove_state(2);
    });

    // Verify that transitions to the removed state are also removed
    auto transitions = fsm.get_available_transitions_in_state(0);
    ASSERT_TRUE(std::find(transitions.begin(), transitions.end(), "to_1") == transitions.end());
}

TEST_F(StateMachineTest, GetNextStateId) {
    int id1 = fsm.get_next_state_id();
    int id2 = fsm.get_next_state_id();
    ASSERT_NE(id1, id2);
    ASSERT_LT(id1, id2);
}

TEST_F(StateMachineTest, AddExistingState) {
    fsm.add_new_state(2);
    ASSERT_THROW(fsm.add_new_state(2), std::runtime_error);
}

TEST_F(StateMachineTest, TriggerNonexistentTransition) {
    ASSERT_THROW(fsm.trigger_transition("nonexistent"), std::runtime_error);
}

TEST_F(StateMachineTest, ResetState) {
    fsm.add_new_state(2);
    fsm.add_transition("to_2", 0, 2);
    fsm.trigger_transition("to_2");
    ASSERT_EQ(fsm.get_current_state(), 2);
    fsm.reset();
    ASSERT_EQ(fsm.get_current_state(), 0);
}

TEST_F(StateMachineTest, GetAllStates) {
    fsm.add_new_state(2);
    fsm.add_new_state(3);
    auto states = fsm.get_all_states();
    ASSERT_EQ(states.size(), 4); // 0, 1, 2, 3
    ASSERT_TRUE(std::find(states.begin(), states.end(), 0) != states.end());
    ASSERT_TRUE(std::find(states.begin(), states.end(), 1) != states.end());
    ASSERT_TRUE(std::find(states.begin(), states.end(), 2) != states.end());
    ASSERT_TRUE(std::find(states.begin(), states.end(), 3) != states.end());
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}