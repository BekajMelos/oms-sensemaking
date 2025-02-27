"""MilSymbol Sensemaker Unit Tests"""
from oms_sensemaking.mil_symbol.converters import to_2525c, to_2525d
from oms_sensemaking.mil_symbol.std_2525c import MilSymbol2525C
from oms_sensemaking.mil_symbol.std_2525d import MilSymbol2525D


def test_convert_to_2525c():

    code_d = MilSymbol2525D("10-0-2-01-5-0-00-000000-00-00")
    assert to_2525c(code_d).formatted_code == "SAAF------*****"

    code_d = MilSymbol2525D("10-0-5-30-1-0-00-000000-00-00")
    assert to_2525c(code_d).formatted_code == "SSSA------*****"

    code_d = MilSymbol2525D("10-0-6-35-3-0-00-000000-00-00")
    assert to_2525c(code_d).formatted_code == "SHUD------*****"

    code_d = MilSymbol2525D("10-0-4-10-2-0-00-000000-00-00")
    assert to_2525c(code_d).formatted_code == "SNGC------*****"


def test_convert_to_2525d():

    code_c = MilSymbol2525C("SAAF------*****")
    assert to_2525d(code_c).formatted_code == "10-0-2-01-5-0-00-000000-00-00"

    code_c = MilSymbol2525C("SSSA------*****")
    assert to_2525d(code_c).formatted_code == "10-0-5-30-1-0-00-000000-00-00"

    code_c = MilSymbol2525C("SHUD------*****")
    assert to_2525d(code_c).formatted_code == "10-0-6-35-3-0-00-000000-00-00"

    code_c = MilSymbol2525C("SNGC------*****")
    assert to_2525d(code_c).formatted_code == "10-0-4-10-2-0-00-000000-00-00"
