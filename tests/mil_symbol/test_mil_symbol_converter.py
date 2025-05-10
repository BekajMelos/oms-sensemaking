"""MilSymbol Sensemaker Unit Tests"""
from oms_sensemaking.mil_symbol.converters import MilSymbol2525B, to_2525c, to_2525c_from_2525b, to_2525d
from oms_sensemaking.mil_symbol.std_2525c import MilSymbol2525C
from oms_sensemaking.mil_symbol.std_2525d import MilSymbol2525D


def test_convert_to_2525c(mil_symbol_rules):

    code_d = MilSymbol2525D("10-0-2-01-5-0-00-000000-00-00", mil_symbol_rules)
    assert to_2525c(code_d, mil_symbol_rules).formatted_code == "SAAF------*****"

    code_d = MilSymbol2525D("10-0-5-30-1-0-00-000000-00-00", mil_symbol_rules)
    assert to_2525c(code_d, mil_symbol_rules).formatted_code == "SSSA------*****"

    code_d = MilSymbol2525D("10-0-6-35-3-0-00-000000-00-00", mil_symbol_rules)
    assert to_2525c(code_d, mil_symbol_rules).formatted_code == "SHUD------*****"

    code_d = MilSymbol2525D("10-0-4-10-2-0-00-000000-00-00", mil_symbol_rules)
    assert to_2525c(code_d, mil_symbol_rules).formatted_code == "SNGC------*****"


def test_convert_to_2525d(mil_symbol_rules):

    code_c = MilSymbol2525C("SAAF------*****", mil_symbol_rules)
    assert to_2525d(code_c, mil_symbol_rules).formatted_code == "10-0-2-01-5-0-00-000000-00-00"

    code_c = MilSymbol2525C("SSSA------*****", mil_symbol_rules)
    assert to_2525d(code_c, mil_symbol_rules).formatted_code == "10-0-5-30-1-0-00-000000-00-00"

    code_c = MilSymbol2525C("SHUD------*****", mil_symbol_rules)
    assert to_2525d(code_c, mil_symbol_rules).formatted_code == "10-0-6-35-3-0-00-000000-00-00"

    code_c = MilSymbol2525C("SNGC------*****", mil_symbol_rules)
    assert to_2525d(code_c, mil_symbol_rules).formatted_code == "10-0-4-10-2-0-00-000000-00-00"

def test_convert_to_2525c_from_2525b(mil_symbol_rules):
    code_b = MilSymbol2525B("SOAF------*****", mil_symbol_rules)
    assert to_2525c_from_2525b(code_b, mil_symbol_rules).formatted_code == "SUAF------*****"

    code_b = MilSymbol2525B("SSSA------*****", mil_symbol_rules)
    assert to_2525c_from_2525b(code_b, mil_symbol_rules).formatted_code == "SSSA------*****"

    code_b = MilSymbol2525B("SOUD------*****", mil_symbol_rules)
    assert to_2525c_from_2525b(code_b, mil_symbol_rules).formatted_code == "SUUD------*****"

    code_b = MilSymbol2525B("SNGC------*****", mil_symbol_rules)
    assert to_2525c_from_2525b(code_b, mil_symbol_rules).formatted_code == "SNGC------*****"
