"""Military Symbol Maker"""

import logging
import re
from typing import Dict

from oms_sensemaking.mil_symbol.mil_symbol_std import MilSymbol
from oms_sensemaking.mil_symbol.std_2525_b_c import MilSymbol2525BandC
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

        symbol_id_code = symbol_id_code.upper()

        trimmed_symbol_id_code = symbol_id_code.replace("-", "")
        if len(trimmed_symbol_id_code) == MIL_SYMBOL_2525D_LENGTH_WITHOUT_DASHES and re.match(
            r"^([\d]{20})$", trimmed_symbol_id_code
        ):
            # recieve 2525D
            return MilSymbol2525D(trimmed_symbol_id_code, settings)

        if len(symbol_id_code) == MIL_SYMBOL_2525BC_LENGTH:
            # The difference between 2525B and 2525C is that B has a "O" affiliation code
            # which means 'none specificied' and this is not present in 2525C or 2525D
            standardized_placeholder_symbol_id_code = symbol_id_code
            for placeholder in MilSymbol2525BandC.MIL_SYM_2525_B_C_PLACEHOLDERS:
                standardized_placeholder_symbol_id_code = standardized_placeholder_symbol_id_code.replace(
                    placeholder, MilSymbol2525BandC.MIL_SYM_2525_B_C_STANDARD_PLACEHOLDER
                )
            if (
                standardized_placeholder_symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_STD_IDENTITY_IDX]
                == MilSymbol2525B.NONE_SPECIFIED_AFFILIATION_CODE
            ):
                # receive 2525B
                return MilSymbol2525B(standardized_placeholder_symbol_id_code, settings)
            else:
                # receive 2525C
                return MilSymbol2525C(standardized_placeholder_symbol_id_code, settings)

        LOGGER.warning(f"Unsupported SIDC for {symbol_id_code}")
        return None
