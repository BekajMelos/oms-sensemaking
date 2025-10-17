import logging
from typing import Dict

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.mil_symbol.std_2525b import MilSymbol2525B
from oms_sensemaking.mil_symbol.std_2525c import MilSymbol2525C
from oms_sensemaking.mil_symbol.std_2525d import MilSymbol2525D

LOGGER = logging.getLogger(__name__)


def to_2525b(code_2525c: MilSymbol2525C, settings: Dict) -> MilSymbol2525B:
    code_2525b = MilSymbol2525B(SETTINGS.mil_symbol_settings.default_2525b_code, settings)

    # convert standard identity, when starting with C, corresponding B will match identity
    standard_identity = code_2525c.code[MilSymbol2525C.MIL_SYM_2525_B_C_STD_IDENTITY_IDX]
    code_2525b.update_code(MilSymbol2525B.MIL_SYM_2525_B_C_STD_IDENTITY_IDX, standard_identity)
    LOGGER.debug("Converted std identity from C to B")

    # convert dimension, when starting with C, corresponding B will match dimension
    dimension = code_2525c.code[MilSymbol2525C.MIL_SYM_2525_B_C_DIMENSION_IDX]
    code_2525b.update_code(MilSymbol2525B.MIL_SYM_2525_B_C_DIMENSION_IDX, dimension)
    LOGGER.debug("Converted dimension from C to B")

    # convert status, when starting with C, corresponding B will match status
    status = code_2525c.code[MilSymbol2525C.MIL_SYM_2525_B_C_STATUS_IDX]
    status_list_c = settings["MIL_SYMBOL_2525C"]["STATUS_LISTS"][status]
    for code, status_list_b in settings["MIL_SYMBOL_2525B"]["STATUS_LISTS"].items():
        if set(status_list_c) & set(status_list_b) and code == status:
            code_2525b.update_code(MilSymbol2525B.MIL_SYM_2525_B_C_STATUS_IDX, status)
            LOGGER.debug("Converted status from C to B")
            break

    # convert sym modifier, when starting with C, corresponding B may/may not match sym modifier
    # Due to command sym modifier codes existing in C, but not in B
    # e.g. AN in C results in ** for B code
    sym_modifier_idx_0 = code_2525c.code[MilSymbol2525C.MIL_SYM_2525_B_C_SYM_MOD_IDX_0]
    sym_modifier_idx_1 = code_2525c.code[MilSymbol2525C.MIL_SYM_2525_B_C_SYM_MOD_IDX_1]
    sym_modifier = sym_modifier_idx_0 + sym_modifier_idx_1
    sym_modifier_list = settings["MIL_SYMBOL_2525C"]["SYMBOL_MODIFIER_LISTS"][sym_modifier]
    for code, other_sym_modifier_list in settings["MIL_SYMBOL_2525B"]["SYMBOL_MODIFIER_LISTS"].items():
        if set(sym_modifier_list) & set(other_sym_modifier_list) and code == sym_modifier:
            code_2525b.update_code(MilSymbol2525B.MIL_SYM_2525_B_C_SYM_MOD_IDX_0, code[0])
            code_2525b.update_code(MilSymbol2525B.MIL_SYM_2525_B_C_SYM_MOD_IDX_1, code[1])
            LOGGER.debug("Converted symbol modifier from C to B")
            break

    # convert order of battle, when startign with C, corresponding B will match order of battle
    ob = code_2525c.code[MilSymbol2525C.MIL_SYM_2525_B_C_ORDER_OF_BATTLE_IDX]
    code_2525b.update_code(MilSymbol2525B.MIL_SYM_2525_B_C_ORDER_OF_BATTLE_IDX, ob)
    LOGGER.debug("Converted order of battle from C to B")

    return code_2525b


def to_2525c(code: MilSymbol2525B | MilSymbol2525D, settings: Dict) -> MilSymbol2525C:
    if isinstance(code, MilSymbol2525B):
        return to_2525c_from_2525b(code, settings)
    elif isinstance(code, MilSymbol2525D):
        return to_2525c_from_2525d(code, settings)
    else:
        raise NotImplementedError("Code type {type(code)} not supported")


def to_2525c_from_2525b(code_2525b: MilSymbol2525B, settings: Dict) -> MilSymbol2525C:
    code_2525c = MilSymbol2525C(SETTINGS.mil_symbol_settings.default_2525c_code, settings)

    # convert standard identity, when starting with B, corresponding C code may/may not match identity
    # Due to none specified code existing in B, but not in C. Mapped to "U" for C
    # e.g. "O" in B code results in "U" for C code
    standard_identity = code_2525b.code[MilSymbol2525B.MIL_SYM_2525_B_C_STD_IDENTITY_IDX]
    standard_identity_list = settings["MIL_SYMBOL_2525B"]["STANDARD_IDENTITY_LISTS"][standard_identity]
    for code, other_standard_identity_list in settings["MIL_SYMBOL_2525C"]["STANDARD_IDENTITY_LISTS"].items():
        # if the lists have values in common then that's the equivalent code
        if set(standard_identity_list) & set(other_standard_identity_list):
            code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_STD_IDENTITY_IDX, code)
            LOGGER.debug("Converted std identity from B to C")
            break

    # convert dimension, when starting with B, corresponding C code will match dimension
    dimension = code_2525b.code[MilSymbol2525B.MIL_SYM_2525_B_C_DIMENSION_IDX]
    code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_DIMENSION_IDX, dimension)
    LOGGER.debug("Converted dimension from B to C")

    # convert status, when starting with B, corresponding C code will match status
    status = code_2525b.code[MilSymbol2525B.MIL_SYM_2525_B_C_STATUS_IDX]
    code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_STATUS_IDX, status)
    LOGGER.debug("Converted status from B to C")

    # convert sym modifier, when starting with B, corresponding C code will match sym modifier
    sym_modifier_idx_0 = code_2525b.code[MilSymbol2525B.MIL_SYM_2525_B_C_SYM_MOD_IDX_0]
    sym_modifier_idx_1 = code_2525b.code[MilSymbol2525B.MIL_SYM_2525_B_C_SYM_MOD_IDX_1]
    sym_modifier = sym_modifier_idx_0 + sym_modifier_idx_1
    code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_SYM_MOD_IDX_0, sym_modifier[0])
    code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_SYM_MOD_IDX_1, sym_modifier[1])
    LOGGER.debug("Converted symbol modifier from B to C")

    # convert order of battle, when starting with B, corresponding C code will mach order of battle
    ob = code_2525b.code[MilSymbol2525B.MIL_SYM_2525_B_C_ORDER_OF_BATTLE_IDX]
    code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_ORDER_OF_BATTLE_IDX, ob)
    LOGGER.debug("Converted order of battle from B to C")

    return code_2525c


def to_2525c_from_2525d(code_2525d: MilSymbol2525D, settings: Dict) -> MilSymbol2525C:
    code_2525c = MilSymbol2525C(SETTINGS.mil_symbol_settings.default_2525c_code, settings)

    # convert standard identity
    standard_identity = code_2525d.code[MilSymbol2525D.MIL_SYM_2525D_STD_IDENTITY_IDX]
    standard_identity_list = settings["MIL_SYMBOL_2525D"]["STANDARD_IDENTITY_LISTS"][standard_identity]
    for code, other_standard_identity_list in settings["MIL_SYMBOL_2525C"]["STANDARD_IDENTITY_LISTS"].items():
        # if the lists have values in common then that's the equivalent code
        if set(standard_identity_list) & set(other_standard_identity_list):
            code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_STD_IDENTITY_IDX, code)
            LOGGER.debug("Converted std identity from D to C")
            break

    # convert dimension
    dimension = (
        code_2525d.code[MilSymbol2525D.MIL_SYM_2525D_DIMENSION_IDX_0]
        + code_2525d.code[MilSymbol2525D.MIL_SYM_2525D_DIMENSION_IDX_1]
    )
    dimension_list = settings["MIL_SYMBOL_2525D"]["DIMENSION_IRIS"][dimension]
    for code, other_dimension_list in settings["MIL_SYMBOL_2525C"]["DIMENSION_IRIS"].items():
        # if the lists have values in common then that's the equivalent code
        if set(dimension_list) & set(other_dimension_list):
            code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_DIMENSION_IDX, code)
            LOGGER.debug("Converted dimension from D to C")
            break

    # convert status
    status = code_2525d.code[MilSymbol2525D.MIL_SYM_2525D_STATUS_IDX]
    status_list = settings["MIL_SYMBOL_2525D"]["STATUS_LISTS"][status]
    for code, other_status_list in settings["MIL_SYMBOL_2525C"]["STATUS_LISTS"].items():
        # if the lists have values in common then that's the equivalent code
        if set(status_list) & set(other_status_list):
            code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_STATUS_IDX, code)
            LOGGER.debug("Converted status from D to C")
            break

    return code_2525c


def to_2525d(code_2525c: MilSymbol2525C, settings: Dict) -> MilSymbol2525D:
    code_2525d = MilSymbol2525D(SETTINGS.mil_symbol_settings.default_2525d_code, settings)

    # convert standard identity
    standard_identity = code_2525c.code[MilSymbol2525C.MIL_SYM_2525_B_C_STD_IDENTITY_IDX]
    standard_identity_list = settings["MIL_SYMBOL_2525C"]["STANDARD_IDENTITY_LISTS"][standard_identity]
    for code, other_standard_identity_list in settings["MIL_SYMBOL_2525D"]["STANDARD_IDENTITY_LISTS"].items():
        # if the lists have values in common then that's the equivalent code
        if set(standard_identity_list) & set(other_standard_identity_list):
            code_2525d.update_code(MilSymbol2525D.MIL_SYM_2525D_STD_IDENTITY_IDX, code)
            LOGGER.debug("Converted std identity from C to D")
            break

    # convert dimension
    dimension = code_2525c.code[MilSymbol2525C.MIL_SYM_2525_B_C_DIMENSION_IDX]
    dimension_list = settings["MIL_SYMBOL_2525C"]["DIMENSION_IRIS"][dimension]
    for code, other_dimension_list in settings["MIL_SYMBOL_2525D"]["DIMENSION_IRIS"].items():
        # if the lists have values in common then that's the equivalent code
        if set(dimension_list) & set(other_dimension_list):
            code_2525d.update_code(MilSymbol2525D.MIL_SYM_2525D_DIMENSION_IDX_0, code[0])
            code_2525d.update_code(MilSymbol2525D.MIL_SYM_2525D_DIMENSION_IDX_1, code[1])
            LOGGER.debug("Converted dimension from C to D")
            break

    # convert status
    status = code_2525c.code[MilSymbol2525C.MIL_SYM_2525_B_C_STATUS_IDX]
    status_list = settings["MIL_SYMBOL_2525C"]["STATUS_LISTS"][status]
    for code, other_status_list in settings["MIL_SYMBOL_2525D"]["STATUS_LISTS"].items():
        # if the lists have values in common then that's the equivalent code
        if set(status_list) & set(other_status_list):
            code_2525d.update_code(MilSymbol2525D.MIL_SYM_2525D_STATUS_IDX, code)
            LOGGER.debug("Converted status from C to D")
            break

    return code_2525d
