"""MilSymbol Sensemaker Unit Tests"""

from oms_sensemaking.mil_symbol.converters import MilSymbol2525B, to_2525b, to_2525c, to_2525d
from oms_sensemaking.mil_symbol.std_2525c import MilSymbol2525C
from oms_sensemaking.mil_symbol.std_2525d import MilSymbol2525D


def test_convert_to_2525c(mil_symbol_rules):
    """Test converting D to C"""

    code_d = MilSymbol2525D("10-0-2-01-5-0-00-000000-00-00", mil_symbol_rules)
    assert to_2525c(code_d, mil_symbol_rules).formatted_code == "SAAF------*****"

    code_d = MilSymbol2525D("10-0-5-30-1-0-00-000000-00-00", mil_symbol_rules)
    assert to_2525c(code_d, mil_symbol_rules).formatted_code == "SSSA------*****"

    code_d = MilSymbol2525D("10-0-6-35-3-0-00-000000-00-00", mil_symbol_rules)
    assert to_2525c(code_d, mil_symbol_rules).formatted_code == "SHUD------*****"

    code_d = MilSymbol2525D("10-0-4-10-2-0-00-000000-00-00", mil_symbol_rules)
    assert to_2525c(code_d, mil_symbol_rules).formatted_code == "SNGC------*****"


def test_convert_to_2525d(mil_symbol_rules):
    """Test converting C to D"""

    code_c = MilSymbol2525C("SAAF------*****", mil_symbol_rules)
    assert to_2525d(code_c, mil_symbol_rules).formatted_code == "10-0-2-01-5-0-00-000000-00-00"

    code_c = MilSymbol2525C("sssa------*****", mil_symbol_rules)
    assert to_2525d(code_c, mil_symbol_rules).formatted_code == "10-0-5-30-1-0-00-000000-00-00"

    code_c = MilSymbol2525C("SHUD------*****", mil_symbol_rules)
    assert to_2525d(code_c, mil_symbol_rules).formatted_code == "10-0-6-35-3-0-00-000000-00-00"

    code_c = MilSymbol2525C("sngc------*****", mil_symbol_rules)
    assert to_2525d(code_c, mil_symbol_rules).formatted_code == "10-0-4-10-2-0-00-000000-00-00"


def test_convert_to_2525c_from_2525b(mil_symbol_rules):
    """Test converting B to C"""

    code_b = MilSymbol2525B("soaf------*****", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUAF------*****"

    code_b = MilSymbol2525B("SsSa------*****", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SSSA------*****"

    code_b = MilSymbol2525B("SOUD------*****", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUUD------*****"

    code_b = MilSymbol2525B("SNGC------*****", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SNGC------*****"

    code_b = MilSymbol2525B("sngc------*****", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SNGC------*****"

    code_b = MilSymbol2525B("sngc------gc***", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SNGC------GC***"

    code_b = MilSymbol2525B("sngc------fM***", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SNGC------FM***"

    code_b = MilSymbol2525B("sngc------*D***", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SNGC------*D***"

    code_b = MilSymbol2525B("sngc------bB***", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SNGC------BB***"

    code_b = MilSymbol2525B("sngc------****a", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SNGC------****A"

    code_b = MilSymbol2525B("sngc------****N", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SNGC------****N"

    code_b = MilSymbol2525B("sngc------****s", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SNGC------****S"


def test_convert_to_2525b(mil_symbol_rules):
    """Test converting C to B"""

    code_c = MilSymbol2525C("suaf------*****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------*****"

    code_c = MilSymbol2525C("SsSa------*****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SSSA------*****"

    code_c = MilSymbol2525C("SUUD------*****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUUD------*****"

    code_c = MilSymbol2525C("SNGC------*****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SNGC------*****"

    code_c = MilSymbol2525C("sngc------*****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SNGC------*****"

    code_c = MilSymbol2525C("suaf------fn***", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------*****"

    code_c = MilSymbol2525C("suaf------GN***", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------*****"

    code_c = MilSymbol2525C("suaf------gI***", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------GI***"

    code_c = MilSymbol2525C("suaf------*a***", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------*A***"

    code_c = MilSymbol2525C("suaf------****G", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------****G"

    code_c = MilSymbol2525C("suaf------****c", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------****C"

    code_c = MilSymbol2525C("suaf------****E", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------****E"
