from .simulator.combatants.bugbear import Bugbear
from .simulator.logging.custom_logger import CustomLogger, LogLevel
from .simulator.session import Session
from .simulator.combatants.dragonclaw_cultist import DragonclawCultist
from .simulator.teams import Teams


def handler(event, context):
    CustomLogger(LogLevel.INFO)
    session = Session()
    session.add_combatant(Bugbear, Teams.Color.RED)
    session.add_combatant(DragonclawCultist, Teams.Color.BLUE)
    session.set_num_simulations(1)
    result = session.simulate(parallel=False)
    return {
        'message': str(result)
    }
