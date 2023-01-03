from simulator.spells.spell import Spell
from simulator.actions import Reaction
import logging

logger = logging.getLogger(__name__)


class Shield(Spell):
    def __init__(self):
        super().__init__(level=1,
                       spell_range=Spell.Range.SELF,
                       target=Spell.Target.SELF,
                       duration=Spell.Duration.INSTANTANEOUS,
                       concentration=False,
                       type=Spell.Type.BUFF,
                       dc=None,
                       dmg_type=None)
        self.action_type = Reaction.SHIELD
