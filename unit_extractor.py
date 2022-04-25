import json
import pint
import re


class ComplexUnit:

    def __init__(self):
        self.numerator_units = list()
        self.denominator_units = list()


class Unit:

    def __init__(self, name, prefix, dimension):
        self.name = name
        self.prefix = prefix
        self.dimension = dimension


def join_patterns(patterns, grouping=False):
    return '(' + ('?:' if not grouping else '') + '|'.join(patterns) + ')'


with open('resources/prefixes.json', 'r', encoding='utf-8') as file:
    prefixes_dict = json.load(file)
with open('resources/units.json', 'r', encoding='utf-8') as file:
    units_dict = json.load(file)
with open('resources/quantities.json', 'r', encoding='utf-8') as file:
    quantites_dict = json.load(file)

WHITE_SPACE = r'[\s\u200c]+'
UNIT = join_patterns(list(units_dict.keys()), True)
PREF = join_patterns(list(prefixes_dict.keys()), True)
UNIT_PREF = rf'(?:(?:{PREF}(?:{WHITE_SPACE})?)?{UNIT})'
UNIT_PREF_DIM = rf'(({UNIT_PREF}({WHITE_SPACE}(مربع|مکعب))?)|(((مربع|مکعب|مجذور){WHITE_SPACE})?{UNIT_PREF}))'
MULT_CONNECTOR = join_patterns([rf'({WHITE_SPACE}(در{WHITE_SPACE})?)', rf'(({WHITE_SPACE})?(\*|×)({WHITE_SPACE})?)'])
UNIT_PREF_DIM_SEQ = rf'({UNIT_PREF_DIM}({MULT_CONNECTOR}{UNIT_PREF_DIM})*)'
DIV_CONNECTOR = join_patterns([rf'({WHITE_SPACE}بر{WHITE_SPACE})', rf'(({WHITE_SPACE})?(\/|÷)({WHITE_SPACE})?)'])
COMPLEX_UNIT = rf'({UNIT_PREF_DIM_SEQ}({DIV_CONNECTOR}{UNIT_PREF_DIM_SEQ})*)'


def unit_to_str(unit):
    prefix = '' if unit.prefix is None else prefixes_dict[unit.prefix]
    return f'({prefix}{units_dict[unit.name]}**{unit.dimension})'


def complex_unit_to_str(complex_unit):
    numerator_str = '(' + '*'.join([unit_to_str(unit) for unit in complex_unit.numerator_units]) + ')'
    denominator_str = '(' + '*'.join([unit_to_str(unit) for unit in complex_unit.denominator_units]) + ')'
    return numerator_str + ('/' + denominator_str if len(complex_unit.denominator_units) > 0 else '')


def unit_to_quantity(unit):
    str = unit_to_str(unit) if isinstance(unit, Unit) else complex_unit_to_str(unit)
    ureg = pint.UnitRegistry()
    dimensionality_dict = dict(ureg(str).dimensionality)
    quantites = []
    for key, value in quantites_dict.items():
        if value == dimensionality_dict:
            quantites.append(key)
    return quantites


def extract_units(text):
    def getComplexUnitInstance(text, level):
        pattern = [COMPLEX_UNIT, UNIT_PREF_DIM_SEQ, UNIT_PREF_DIM, UNIT_PREF][level]
        matches = [match for match in re.finditer(pattern, text)]
        if level == 0:
            return [{
                'marker': match.group(),
                'span': match.span(),
                'object': getComplexUnitInstance(match.group(), 1)
            } for match in matches]
        if level == 1:
            complexUnit = ComplexUnit()
            complexUnit.numerator_units = getComplexUnitInstance(matches[0].group(), 2)
            if len(matches) > 1:
                for match in matches[1:]:
                    for unit in getComplexUnitInstance(match.group(), 2):
                        complexUnit.denominator_units.append(unit)
            return complexUnit
        if level == 2:
            return [getComplexUnitInstance(match.group(), 3) for match in matches]
        if level == 3:
            dimension = 1
            if re.findall("مجذور|مربع", text):
                dimension = 2
            if re.findall("مکعب", text):
                dimension = 3
            prefix, name = tuple(re.search(UNIT_PREF, matches[0].group()).groups())
            return Unit(name, prefix, dimension)

    return getComplexUnitInstance(text, 0)
