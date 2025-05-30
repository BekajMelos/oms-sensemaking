"""Military Symbol Standard 2525B"""

import logging

from oms_sensemaking.mil_symbol.std_2525_b_c import MilSymbol2525BandC

LOGGER = logging.getLogger(__name__)

class MilSymbol2525B(MilSymbol2525BandC):
    """Class for MIL-STD-2525B format SIDCs"""
    NONE_SPECIFIED_AFFILIATION_CODE = "O"
    code_type_config = "MIL_SYMBOL_2525B"
