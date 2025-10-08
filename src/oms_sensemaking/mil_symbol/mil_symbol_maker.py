"""Military Symbol Maker"""

import logging
from typing import Dict

from oms_sensemaking.mil_symbol.mil_symbol_std import MilSymbol
from oms_sensemaking.mil_symbol.mil_symbol_validator import (
    MilSymbol2525BValidator,
    MilSymbol2525CValidator,
    MilSymbol2525DValidator,
)
from oms_sensemaking.mil_symbol.std_2525b import MilSymbol2525B
from oms_sensemaking.mil_symbol.std_2525c import MilSymbol2525C
from oms_sensemaking.mil_symbol.std_2525d import MilSymbol2525D

LOGGER = logging.getLogger(__name__)

MIL_SYMBOL_2525D_LENGTH_WITHOUT_DASHES = 20
MIL_SYMBOL_2525BC_LENGTH = 15


class MilSymbolMaker:
    """Class used to create Mil Symbol objects"""

    @staticmethod
    def make(symbol_id_code: str, settings: Dict) -> MilSymbol | None:
        """Create a MilSymbol2525B, MilSymbol2525C, or MilSymbol2525D based on the code

        :param symbol_id_code: Symbol id code to create an object from
        :param settings: Mil Symbol Rules
        """
        try:
            symbol_id_code = symbol_id_code.upper()

            trimmed_symbol_id_code = symbol_id_code.replace("-", "")
            if MilSymbol2525DValidator.is_valid(trimmed_symbol_id_code, settings):
                # recieve 2525D
                return MilSymbol2525D(trimmed_symbol_id_code, settings)
            elif (
                symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_STD_IDENTITY_IDX]
                == MilSymbol2525B.NONE_SPECIFIED_AFFILIATION_CODE
            ) and MilSymbol2525BValidator.is_valid(symbol_id_code, settings):
                # recieve 2525B
                return MilSymbol2525B(symbol_id_code, settings)
            elif MilSymbol2525CValidator.is_valid(symbol_id_code, settings):
                # recieve 2525C
                return MilSymbol2525C(symbol_id_code, settings)
        except KeyError:
            LOGGER.warning(f"Unsupported SIDC for {symbol_id_code}")
            return None
        return None
