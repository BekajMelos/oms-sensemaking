"""Military Symbol Standard 2525C"""

import logging

from oms_sensemaking.mil_symbol.std_2525_b_c import MilSymbol2525BandC

LOGGER = logging.getLogger(__name__)


class MilSymbol2525C(MilSymbol2525BandC):
    CODE_TYPE_CONFIG = "MIL_SYMBOL_2525C"
