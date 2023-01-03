from simulator.spells.spell import Spell
from simulator.misc import DamageType
from simulator.actions import Action
import logging

logger = logging.getLogger(__name__)
class Chaosbolt(Spell):

    DMG_TYPE = (DamageType.Acid, DamageType.Cold, DamageType.Fire, DamageType.Force, DamageType.Lightning, DamageType.Poison, DamageType.Psychic,
                DamageType.Thunder)
    def __init__(self, to_hit, targets):
        super().__init__(level=1,
                         spell_range=Spell.Range.FEET_120,
                         target=Spell.Target.ONE_CREATURE,
                         duration=Spell.Duration.INSTANTANEOUS,
                         concentration=False,
                         type=Spell.Type.HARMFUL,
                         dc=None,
                         dmg_type=None)
        self.action_type = Action.CHAOSBOLT
        self.to_hit = to_hit
        self.targets = targets
