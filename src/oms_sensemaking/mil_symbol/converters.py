import logging
from typing import Dict

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.mil_symbol.std_2525b import MilSymbol2525B
from oms_sensemaking.mil_symbol.std_2525c import MilSymbol2525C
from oms_sensemaking.mil_symbol.std_2525d import MilSymbol2525D

LOGGER = logging.getLogger(__name__)

def to_2525c(code: MilSymbol2525B | MilSymbol2525D, settings: Dict) -> MilSymbol2525C:
    if isinstance(code, MilSymbol2525B):
        return to_2525c_from_2525b(code, settings)
    elif isinstance(code, MilSymbol2525D):
        return to_2525c_from_2525d(code, settings)
    else:
        raise NotImplementedError(f"Code type {type(code)} not supported")


def to_2525c_from_2525b(code_2525b: MilSymbol2525B, settings: Dict) -> MilSymbol2525C:

        code_2525c = MilSymbol2525C(code_2525b.code, settings)

        # convert standard identity
        standard_identity = code_2525b.code[MilSymbol2525B.MIL_SYM_2525_B_C_STD_IDENTITY_IDX]
        standard_identity_list = settings["MIL_SYMBOL_2525B"]["STANDARD_IDENTITY_LISTS"][standard_identity]
        for code, other_standard_identity_list in settings["MIL_SYMBOL_2525C"]["STANDARD_IDENTITY_LISTS"].items():
            # if the lists have values in common then that's the equivalent code
            if set(standard_identity_list) & set(other_standard_identity_list):
                code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_STD_IDENTITY_IDX, code)
                LOGGER.debug(f'Equivalent std identity is : {code} b/c {other_standard_identity_list}')
                break

        # convert dimension
        dimension = code_2525b.code[MilSymbol2525B.MIL_SYM_2525_B_C_DIMENSION_IDX]
        code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_DIMENSION_IDX, dimension)
        LOGGER.debug(f'Equivalent dimension is : {dimension}, 2525b & 2525c share dimension')

        # convert status
        status = code_2525b.code[MilSymbol2525B.MIL_SYM_2525_B_C_STATUS_IDX]
        code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_STATUS_IDX, status)
        LOGGER.debug(f'Equivalent status is : {code}, 2525b & 2525c share status')

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
                LOGGER.debug(f'Equivalent std identity is : {code} b/c {other_standard_identity_list}')
                break

        # convert dimension
        dimension = (code_2525d.code[MilSymbol2525D.MIL_SYM_2525D_DIMENSION_IDX_0] +
                     code_2525d.code[MilSymbol2525D.MIL_SYM_2525D_DIMENSION_IDX_1])
        dimension_list = settings["MIL_SYMBOL_2525D"]["DIMENSION_IRIS"][dimension]
        for code, other_dimension_list in settings["MIL_SYMBOL_2525C"]["DIMENSION_IRIS"].items():
            # if the lists have values in common then that's the equivalent code
            if set(dimension_list) & set(other_dimension_list):
                code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_DIMENSION_IDX, code)
                LOGGER.debug(f'Equivalent dimension is : {code} b/c {other_dimension_list}')
                break

        # convert status
        status = code_2525d.code[MilSymbol2525D.MIL_SYM_2525D_STATUS_IDX]
        status_list = settings["MIL_SYMBOL_2525D"]["STATUS_LISTS"][status]
        for code, other_status_list in settings["MIL_SYMBOL_2525C"]["STATUS_LISTS"].items():
            # if the lists have values in common then that's the equivalent code
            if set(status_list) & set(other_status_list):
                code_2525c.update_code(MilSymbol2525C.MIL_SYM_2525_B_C_STATUS_IDX, code)
                LOGGER.debug(f'Equivalent status is : {code} b/c {other_status_list}')
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
            LOGGER.debug(f'Equivalent std identity is : {code} b/c {other_standard_identity_list}')
            break

    # convert dimension
    dimension = code_2525c.code[MilSymbol2525C.MIL_SYM_2525_B_C_DIMENSION_IDX]
    dimension_list = settings["MIL_SYMBOL_2525C"]["DIMENSION_IRIS"][dimension]
    for code, other_dimension_list in settings["MIL_SYMBOL_2525D"]["DIMENSION_IRIS"].items():
        # if the lists have values in common then that's the equivalent code
        if set(dimension_list) & set(other_dimension_list):
            code_2525d.update_code(MilSymbol2525D.MIL_SYM_2525D_DIMENSION_IDX_0, code[0])
            code_2525d.update_code(MilSymbol2525D.MIL_SYM_2525D_DIMENSION_IDX_1, code[1])
            LOGGER.debug(f'Equivalent dimension is : {code} b/c {other_dimension_list}')
            break

    # convert status
    status = code_2525c.code[MilSymbol2525C.MIL_SYM_2525_B_C_STATUS_IDX]
    status_list = settings["MIL_SYMBOL_2525C"]["STATUS_LISTS"][status]
    for code, other_status_list in settings["MIL_SYMBOL_2525D"]["STATUS_LISTS"].items():
        # if the lists have values in common then that's the equivalent code
        if set(status_list) & set(other_status_list):
            code_2525d.update_code(MilSymbol2525D.MIL_SYM_2525D_STATUS_IDX, code)
            LOGGER.debug(f'Equivalent status is : {code} b/c {other_status_list}')
            break

    return code_2525d
