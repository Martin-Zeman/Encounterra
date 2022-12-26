from simulator.spells.spell import Spell
import logging

logger = logging.getLogger(__name__)
class Shield(Spell):
    def __init__(self):
        super().__init__(level=1,
                         casting_time=Spell.CastingTime.REACTION,
                         spell_range=Spell.Range.SELF,
                         target=Spell.Target.SELF,
                         duration=Spell.Duration.INSTANTANEOUS,
                         concentration=False,
                         type=Spell.Type.BUFF,
                         dc=None,
                         dmg_type=None)
