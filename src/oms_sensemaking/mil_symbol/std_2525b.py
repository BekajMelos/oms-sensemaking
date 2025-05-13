"""Military Symbol Standard 2525B"""

import logging

from oms_sensemaking.mil_symbol.std_2525_b_c import MilSymbol2525BandC

LOGGER = logging.getLogger(__name__)

class MilSymbol2525B(MilSymbol2525BandC):
    NONE_SPECIFIED_AFFILIATION_CODE = "O"
    CODE_TYPE_CONFIG = "MIL_SYMBOL_2525B"
