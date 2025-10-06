"""Military Symbol Maker"""

import logging
import re
from typing import Dict

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.mil_symbol.mil_symbol_std import MilSymbol
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
            if (
                symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_STD_IDENTITY_IDX]
                == MilSymbol2525B.NONE_SPECIFIED_AFFILIATION_CODE
            ):
                # receive 2525B
                b_code = MilSymbol2525B(symbol_id_code, settings)
                if (
                    b_code.code[MilSymbol2525B.MIL_SYM_2525_B_C_STATUS_IDX]
                    == MilSymbol2525B.INVALID_UNKNOWN_STATUS_CODE
                ):
                    b_code.update_code(
                        MilSymbol2525C.MIL_SYM_2525_B_C_STATUS_IDX, SETTINGS.mil_symbol_settings.b_c_placeholders[1]
                    )
                return b_code
            else:
                # receive 2525C
                c_code = MilSymbol2525C(symbol_id_code, settings)
                if (
                    c_code.code[MilSymbol2525C.MIL_SYM_2525_B_C_STATUS_IDX]
                    == MilSymbol2525C.INVALID_UNKNOWN_STATUS_CODE
                ):
                    c_code.update_code(
                        MilSymbol2525C.MIL_SYM_2525_B_C_STATUS_IDX, SETTINGS.mil_symbol_settings.b_c_placeholders[1]
                    )
                return c_code

        LOGGER.warning(f"Unsupported SIDC for {symbol_id_code}")
        return None
