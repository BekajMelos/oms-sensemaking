"""MilSymbol Sensemaker Unit Tests"""

from oms_sensemaking.mil_symbol.converters import to_2525b, to_2525c, to_2525d
from oms_sensemaking.mil_symbol.mil_symbol_maker import MilSymbolMaker
from oms_sensemaking.mil_symbol.std_2525b import MilSymbol2525B


def test_convert_to_2525c(mil_symbol_rules):
    """Test converting D to C"""

    code_d = MilSymbolMaker.make("10-0-2-01-5-0-00-000000-00-00", mil_symbol_rules)
    assert to_2525c(code_d, mil_symbol_rules).formatted_code == "SAAF------*****"

    code_d = MilSymbolMaker.make("10-0-5-30-1-0-00-000000-00-00", mil_symbol_rules)
    assert to_2525c(code_d, mil_symbol_rules).formatted_code == "SSSA------*****"

    code_d = MilSymbolMaker.make("10-0-6-35-3-0-00-000000-00-00", mil_symbol_rules)
    assert to_2525c(code_d, mil_symbol_rules).formatted_code == "SHUD------*****"

    code_d = MilSymbolMaker.make("10-0-4-10-2-0-00-000000-00-00", mil_symbol_rules)
    assert to_2525c(code_d, mil_symbol_rules).formatted_code == "SNGC------*****"


def test_convert_to_2525d(mil_symbol_rules):
    """Test converting C to D"""

    code_c = MilSymbolMaker.make("SAAF------*****", mil_symbol_rules)
    assert to_2525d(code_c, mil_symbol_rules).formatted_code == "10-0-2-01-5-0-00-000000-00-00"

    code_c = MilSymbolMaker.make("sssa------*****", mil_symbol_rules)
    assert to_2525d(code_c, mil_symbol_rules).formatted_code == "10-0-5-30-1-0-00-000000-00-00"

    code_c = MilSymbolMaker.make("SHUD------*****", mil_symbol_rules)
    assert to_2525d(code_c, mil_symbol_rules).formatted_code == "10-0-6-35-3-0-00-000000-00-00"

    code_c = MilSymbolMaker.make("sngc------*****", mil_symbol_rules)
    assert to_2525d(code_c, mil_symbol_rules).formatted_code == "10-0-4-10-2-0-00-000000-00-00"


def test_convert_to_2525c_from_2525b(mil_symbol_rules):
    """Test converting B to C"""

    code_b = MilSymbolMaker.make("soaf------*****", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUAF------*****"

    code_b = MilSymbolMaker.make("SoSa------*****", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUSA------*****"

    code_b = MilSymbolMaker.make("SOUD------*****", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUUD------*****"

    code_b = MilSymbolMaker.make("SoGC------*****", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUGC------*****"

    code_b = MilSymbolMaker.make("sOgc------*****", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUGC------*****"

    code_b = MilSymbolMaker.make("sog*------*****", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUG*------*****"

    # Using MilSymbol2525B constructor since MilSymbolMaker will default any B/C code without
    # a "O" code for standard identity as a C code which was intended since any B code
    # without an "O" is a C code. Wanted to test mapping for "*" to 'unknown
    code_b = MilSymbol2525B("s*gc------*****", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUGC------*****"

    code_b = MilSymbolMaker.make("so**------*****", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SU**------*****"


def test_convert_to_2525c_from_2525b_sym_mod(mil_symbol_rules):
    code_b = MilSymbolMaker.make("sogc------gc***", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUGC------GC***"

    code_b = MilSymbolMaker.make("sOgc------fM***", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUGC------FM***"

    code_b = MilSymbolMaker.make("sogc-------D***", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUGC-------D***"

    code_b = MilSymbolMaker.make("sogc--------***", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUGC--------***"

    code_b = MilSymbolMaker.make("sogc-------k***", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUGC-------K***"

    code_b = MilSymbolMaker.make("sOgc------bB***", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUGC------BB***"

    code_b = MilSymbolMaker.make("sOgc------A-***", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUGC------A-***"


def test_convert_to_2525c_from_2525b_ob(mil_symbol_rules):
    code_b = MilSymbolMaker.make("sOgc------****a", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUGC------****A"

    code_b = MilSymbolMaker.make("sOgc------****N", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUGC------****N"

    code_b = MilSymbolMaker.make("sogc------****s", mil_symbol_rules)
    assert to_2525c(code_b, mil_symbol_rules).formatted_code == "SUGC------****S"


def test_convert_to_2525b(mil_symbol_rules):
    """Test converting C to B"""

    code_c = MilSymbolMaker.make("suaf------*****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------*****"

    code_c = MilSymbolMaker.make("SsSa------*****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SSSA------*****"

    code_c = MilSymbolMaker.make("SUUD------*****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUUD------*****"

    code_c = MilSymbolMaker.make("SNGC------*****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SNGC------*****"

    code_c = MilSymbolMaker.make("sngc------*****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SNGC------*****"

    code_c = MilSymbolMaker.make("s---------*****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "S---------*****"

    code_c = MilSymbolMaker.make("s***------*****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "S***------*****"

    code_c = MilSymbolMaker.make("s*Z*------*****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "S*Z*------*****"


def test_convert_to_2525b_sym_mod(mil_symbol_rules):
    code_c = MilSymbolMaker.make("suaf------fn***", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------*****"

    code_c = MilSymbolMaker.make("suaf------GN***", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------*****"

    code_c = MilSymbolMaker.make("suaf------gI***", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------GI***"

    code_c = MilSymbolMaker.make("suaf-------a***", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF-------A***"

    code_c = MilSymbolMaker.make("suaf-------b***", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF-------B***"

    code_c = MilSymbolMaker.make("suaf------b****", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------B****"


def test_convert_to_2525b_ob(mil_symbol_rules):
    code_c = MilSymbolMaker.make("suaf------****G", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------****G"

    code_c = MilSymbolMaker.make("suaf------****c", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------****C"

    code_c = MilSymbolMaker.make("suaf------****E", mil_symbol_rules)
    assert to_2525b(code_c, mil_symbol_rules).formatted_code == "SUAF------****E"
