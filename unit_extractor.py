import re
import pint


class ComplexUnit:

    def __init__(self):
        self.numerator_units = list()
        self.denominator_units = list()
        self.dimensionality = None


class Unit:

    def __init__(self, name, prefix, dimensionality):
        self.name = name
        self.prefix = prefix
        self.dimensionality = dimensionality


def join_patterns(patterns, grouping=False):
    return '(' + ('?:' if not grouping else '') + '|'.join(patterns) + ')'


WHITE_SPACE = r'[\s\u200c]+'

UNIT = join_patterns(list(units.keys()), True)  # TODO: A function to get all units
PREF = join_patterns(list(prefixes.keys()), True)  # TODO: A function to get all prefixes
UNIT_PREF = rf'(?:(?:{PREF}(?:{WHITE_SPACE})?)?{UNIT})'
UNIT_PREF_DIM = rf'(({UNIT_PREF}({WHITE_SPACE}(مربع|مکعب))?)|(((مربع|مکعب|مجذور){WHITE_SPACE})?{UNIT_PREF}))'
MULT_CONNECTOR = join_patterns([rf'({WHITE_SPACE}(در{WHITE_SPACE})?)', rf'(({WHITE_SPACE})?(\*|×)({WHITE_SPACE})?)'])
UNIT_PREF_DIM_SEQ = rf'({UNIT_PREF_DIM}({MULT_CONNECTOR}{UNIT_PREF_DIM})*)'
DIV_CONNECTOR = join_patterns([rf'({WHITE_SPACE}بر{WHITE_SPACE})', rf'(({WHITE_SPACE})?(\/|÷)({WHITE_SPACE})?)'])
COMPLEX_UNIT = rf'({UNIT_PREF_DIM_SEQ}({DIV_CONNECTOR}{UNIT_PREF_DIM_SEQ})*)'


def sing_unit_to_str(unit):
    pr = '' if unit.prefix is None else prefixes[unit.prefix]
    dim = 1 if unit.dimensionality is None else int(unit.dimensionality.split('**')[1])
    return f'({pr}{units[unit.name]}**{dim})'


def unit_to_str(complex_unit):
    num = '(' + '*'.join([sing_unit_to_str(unit) for unit in complex_unit.numerator_units]) + ')'
    den = '(' + '*'.join([sing_unit_to_str(unit) for unit in complex_unit.denominator_units]) + ')'
    return num + '/' + den


def extract_units(text):
    def getComplexUnitInstance(text, level):
        pattern = [COMPLEX_UNIT, UNIT_PREF_DIM_SEQ, UNIT_PREF_DIM, UNIT_PREF][level]
        matches = [match for match in re.finditer(pattern, text)]
        if level == 0:
            print("level 0", matches)
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
            power = 1
            if re.findall("مجذور|مربع", text):
                power = 2
            if re.findall("مکعب", text):
                power = 3
            prefix, name = tuple(re.search(UNIT_PREF, matches[0].group()).groups())
            dimensionality = f"[length] ** {power}"
            return Unit(name, prefix, dimensionality)

    return getComplexUnitInstance(text, 0)
