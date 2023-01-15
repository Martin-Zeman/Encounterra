from simulator.spells.spell import Spell
from simulator.misc import DamageType
from simulator.action_types import Action, BonusAction
import logging

logger = logging.getLogger(__name__)


class Chaosbolt(Spell):
    DMG_TYPE = (
        DamageType.Acid, DamageType.Cold, DamageType.Fire, DamageType.Force, DamageType.Lightning, DamageType.Poison, DamageType.Psychic,
        DamageType.Thunder)

    def __init__(self, action_type, to_hit, targets, **kwargs):
        super().__init__(level=1,
                         spell_range=Spell.Range.FEET_120,
                         target=Spell.Target.ONE_CREATURE,
                         duration=Spell.Duration.INSTANTANEOUS,
                         concentration=False,
                         type=Spell.Type.HARMFUL,
                         dc=None,
                         dmg_type=None)
        self.action_type = action_type
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.to_hit = to_hit
        self.targets = targets
        self.dmg_dice = "2d8"
        self.additional_dmg_dice = "1d6"
