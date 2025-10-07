"""Military Symbol Maker"""

import logging
import re
from typing import Dict

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
        try:
            symbol_id_code = symbol_id_code.upper()

            trimmed_symbol_id_code = symbol_id_code.replace("-", "")
            if len(trimmed_symbol_id_code) == MIL_SYMBOL_2525D_LENGTH_WITHOUT_DASHES and re.match(
                r"^([\d]{20})$", trimmed_symbol_id_code
            ):
                # recieve 2525D
                MilSymbolMaker.check_valid_starting_symid(trimmed_symbol_id_code, "d", settings)
                return MilSymbol2525D(trimmed_symbol_id_code, settings)

            if len(symbol_id_code) == MIL_SYMBOL_2525BC_LENGTH:
                # The difference between 2525B and 2525C is that B has a "O" affiliation code
                # which means 'none specificied' and this is not present in 2525C or 2525D
                if (
                    symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_STD_IDENTITY_IDX]
                    == MilSymbol2525B.NONE_SPECIFIED_AFFILIATION_CODE
                ):
                    # receive 2525B
                    MilSymbolMaker.check_valid_starting_symid(symbol_id_code, "b", settings)
                    return MilSymbol2525B(symbol_id_code, settings)
                else:
                    # receive 2525C
                    MilSymbolMaker.check_valid_starting_symid(symbol_id_code, "c", settings)
                    return MilSymbol2525C(symbol_id_code, settings)
        except KeyError:
            LOGGER.warning(f"Unsupported SIDC for {symbol_id_code}")
            return None
        return None

    @staticmethod
    def check_valid_starting_symid(symbol_id_code: str, format_flag: str, settings: Dict) -> None:
        if format_flag == "d":
            if (
                symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_CONTEXT_IDX]
                not in settings["MIL_SYMBOL_2525D"]["CONTEXT_LISTS"]
                or symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_STD_IDENTITY_IDX]
                not in settings["MIL_SYMBOL_2525D"]["STANDARD_IDENTITY_LISTS"]
                or (
                    symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_DIMENSION_IDX_0]
                    + symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_DIMENSION_IDX_1]
                )
                not in settings["MIL_SYMBOL_2525D"]["DIMENSION_IRIS"]
                or symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_STATUS_IDX]
                not in settings["MIL_SYMBOL_2525D"]["STATUS_LISTS"]
                or (
                    symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_AMPLIFIER_IDX_0]
                    + symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_AMPLIFIER_IDX_1]
                )
                not in settings["MIL_SYMBOL_2525D"]["AMPLIFIER_LISTS"]
            ):
                raise KeyError("Invalid starting 2525D symbol Id code")
        elif format_flag == "b":
            if (
                symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_STD_IDENTITY_IDX]
                not in settings["MIL_SYMBOL_2525B"]["STANDARD_IDENTITY_LISTS"]
                or symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_DIMENSION_IDX]
                not in settings["MIL_SYMBOL_2525B"]["DIMENSION_IRIS"]
                or symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_STATUS_IDX]
                not in settings["MIL_SYMBOL_2525B"]["STATUS_LISTS"]
                or (
                    symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_SYM_MOD_IDX_0]
                    + symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_SYM_MOD_IDX_1]
                )
                not in settings["MIL_SYMBOL_2525B"]["SYMBOL_MODIFIER_LISTS"]
                or symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_ORDER_OF_BATTLE_IDX]
                not in settings["MIL_SYMBOL_2525B"]["ORDER_OF_BATTLE"]
            ):
                raise KeyError("Invalid starting 2525B symbol Id code")
        else:
            if (
                symbol_id_code[MilSymbol2525C.MIL_SYM_2525_B_C_STD_IDENTITY_IDX]
                not in settings["MIL_SYMBOL_2525C"]["STANDARD_IDENTITY_LISTS"]
                or symbol_id_code[MilSymbol2525C.MIL_SYM_2525_B_C_DIMENSION_IDX]
                not in settings["MIL_SYMBOL_2525C"]["DIMENSION_IRIS"]
                or symbol_id_code[MilSymbol2525C.MIL_SYM_2525_B_C_STATUS_IDX]
                not in settings["MIL_SYMBOL_2525C"]["STATUS_LISTS"]
                or (
                    symbol_id_code[MilSymbol2525C.MIL_SYM_2525_B_C_SYM_MOD_IDX_0]
                    + symbol_id_code[MilSymbol2525C.MIL_SYM_2525_B_C_SYM_MOD_IDX_1]
                )
                not in settings["MIL_SYMBOL_2525C"]["SYMBOL_MODIFIER_LISTS"]
                or symbol_id_code[MilSymbol2525C.MIL_SYM_2525_B_C_ORDER_OF_BATTLE_IDX]
                not in settings["MIL_SYMBOL_2525C"]["ORDER_OF_BATTLE"]
            ):
                raise KeyError("Invalid starting 2525C symbol Id code")
        return None
