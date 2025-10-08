import logging
import re
from typing import Dict

from oms_sensemaking.mil_symbol.std_2525b import MilSymbol2525B
from oms_sensemaking.mil_symbol.std_2525c import MilSymbol2525C
from oms_sensemaking.mil_symbol.std_2525d import MilSymbol2525D

LOGGER = logging.getLogger(__name__)

MIL_SYMBOL_2525D_LENGTH_WITHOUT_DASHES = 20
MIL_SYMBOL_2525BC_LENGTH = 15


class MilSymbol2525BValidator:
    @staticmethod
    def is_valid(symbol_id_code: str, settings: Dict) -> bool:
        if len(symbol_id_code) == MIL_SYMBOL_2525BC_LENGTH and (
            symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_STD_IDENTITY_IDX]
            in settings["MIL_SYMBOL_2525B"]["STANDARD_IDENTITY_LISTS"]
            and symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_DIMENSION_IDX]
            in settings["MIL_SYMBOL_2525B"]["DIMENSION_IRIS"]
            and symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_STATUS_IDX]
            in settings["MIL_SYMBOL_2525B"]["STATUS_LISTS"]
            and (
                symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_SYM_MOD_IDX_0]
                + symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_SYM_MOD_IDX_1]
            )
            in settings["MIL_SYMBOL_2525B"]["SYMBOL_MODIFIER_LISTS"]
            and symbol_id_code[MilSymbol2525B.MIL_SYM_2525_B_C_ORDER_OF_BATTLE_IDX]
            in settings["MIL_SYMBOL_2525B"]["ORDER_OF_BATTLE"]
        ):
            return True
        LOGGER.warning(f"Invalid starting 2525B symbol Id code: {symbol_id_code}")
        return False


class MilSymbol2525CValidator:
    @staticmethod
    def is_valid(symbol_id_code: str, settings: Dict) -> bool:
        if len(symbol_id_code) == MIL_SYMBOL_2525BC_LENGTH and (
            symbol_id_code[MilSymbol2525C.MIL_SYM_2525_B_C_STD_IDENTITY_IDX]
            in settings["MIL_SYMBOL_2525C"]["STANDARD_IDENTITY_LISTS"]
            and symbol_id_code[MilSymbol2525C.MIL_SYM_2525_B_C_DIMENSION_IDX]
            in settings["MIL_SYMBOL_2525C"]["DIMENSION_IRIS"]
            and symbol_id_code[MilSymbol2525C.MIL_SYM_2525_B_C_STATUS_IDX]
            in settings["MIL_SYMBOL_2525C"]["STATUS_LISTS"]
            and (
                symbol_id_code[MilSymbol2525C.MIL_SYM_2525_B_C_SYM_MOD_IDX_0]
                + symbol_id_code[MilSymbol2525C.MIL_SYM_2525_B_C_SYM_MOD_IDX_1]
            )
            in settings["MIL_SYMBOL_2525C"]["SYMBOL_MODIFIER_LISTS"]
            and symbol_id_code[MilSymbol2525C.MIL_SYM_2525_B_C_ORDER_OF_BATTLE_IDX]
            in settings["MIL_SYMBOL_2525C"]["ORDER_OF_BATTLE"]
        ):
            return True
        LOGGER.warning(f"Invalid starting 2525C symbol Id code: {symbol_id_code}")
        return False


class MilSymbol2525DValidator:
    @staticmethod
    def is_valid(symbol_id_code: str, settings: Dict) -> bool:
        if (
            len(symbol_id_code) == MIL_SYMBOL_2525D_LENGTH_WITHOUT_DASHES
            and re.match(r"^([\d]{20})$", symbol_id_code)
            and (
                symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_CONTEXT_IDX]
                in settings["MIL_SYMBOL_2525D"]["CONTEXT_LISTS"]
                and symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_STD_IDENTITY_IDX]
                in settings["MIL_SYMBOL_2525D"]["STANDARD_IDENTITY_LISTS"]
                and (
                    symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_DIMENSION_IDX_0]
                    + symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_DIMENSION_IDX_1]
                )
                in settings["MIL_SYMBOL_2525D"]["DIMENSION_IRIS"]
                and symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_STATUS_IDX]
                in settings["MIL_SYMBOL_2525D"]["STATUS_LISTS"]
                and (
                    symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_AMPLIFIER_IDX_0]
                    + symbol_id_code[MilSymbol2525D.MIL_SYM_2525D_AMPLIFIER_IDX_1]
                )
                in settings["MIL_SYMBOL_2525D"]["AMPLIFIER_LISTS"]
            )
        ):
            return True
        LOGGER.warning(f"Invalid starting 2525D symbol Id code: {symbol_id_code}")
        return False
