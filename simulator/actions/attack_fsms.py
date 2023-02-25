from statemachine import State, StateMachine
class TwoMeleeOneRangedWithReckless(StateMachine):
    A = State("A", (1, 2, 3), initial=True)  # not attacked yet
    B = State("B", (1,))  # attacked with melee
    C = State("C", (2,))  # attacked with melee recklessly
    nop = State("nop", value=(), final=True)
    melee = A.to(B) | B.to(nop)
    melee_recklessly = A.to(C) | C.to(nop)
    ranged = A.to(nop)


class TwoMeleeOneRanged(StateMachine):
    A = State("A", value=(1, 2), initial=True)  # not attacked yet
    B = State("B", value=(1,))  # attacked once
    nop = State("nop", value=(),final=True)
    melee = A.to(B) | B.to(nop)
    ranged = A.to(nop)

class OneAttack(StateMachine):
    A = State("A", value=(1,), initial=True)  # not attacked yet
    nop = State("nop", value=(), final=True)
    attack = A.to(nop)


class OneMeleeOrOneRanged(StateMachine):
    A = State("A", value=(1,2), initial=True)  # not attacked yet
    nop = State("nop", value=(), final=True)
    melee = A.to(nop)
    ranged = A.to(nop)
