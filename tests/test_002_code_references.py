import pytest
import random

CODE_REGEX = {
    "CCIV": r"(?P<CCIV>Code civil|C\.\sciv\.|Code\sciv\.|C\.civ\.|civ\.|CCIV)",
    "CPRCIV": r"(?P<CPRCIV>Code\sde\sprocédure civile|C\.\spr\.\sciv\.|CPC)",
    "CCOM": r"(?P<CCOM>Code\sde\scommerce|C\.\scom\.)",
    "CTRAV": r"(?P<CTRAV>Code\sdu\stravail|C\.\strav\.)",
    "CPI": r"(?P<CPI>Code\sde\sla\spropriété\sintellectuelle|CPI|C\.\spr\.\sint\.)",
    "CPEN": r"(?P<CPEN>Code\spénal|C\.\spén\.)",
    "CPP": r"(?P<CPP>Code\sde\sprocédure\spénale|CPP)",
    "CASSUR": r"(?P<CASSUR>Code\sdes\sassurances|C\.\sassur\.)",
    "CCONSO": r"(?P<CCONSO>Code\sde\sla\sconsommation|C\.\sconso\.)",
    "CSI": r"(?P<CSI>Code\sde\slasécurité intérieure|CSI)",
    "CSP": r"(?P<CSP>Code\sde\slasanté publique|C\.\ssant\.\spub\.|CSP)",
    "CSS": r"(?P<CSS>Code\sde\slasécurité sociale|C\.\ssec\.\ssoc\.|CSS)",
    "CESEDA": r"(?P<CESEDA>Code\sde\sl'entrée\set\sdu\sséjour\sdes\sétrangers\set\sdu\sdroit\sd'asile|CESEDA)",
    "CGCT": r"(?P<CGCT>Code\sgénéral\sdes\scollectivités\sterritoriales|CGCT)",
    "CPCE": r"(?P<CPCE>Code\sdes\spostes\set\sdes\scommunications\sélectroniques|CPCE)",
    "CENV": r"(?P<CENV>Code\sde\sl'environnement|C.\senvir.|\sCE\.?\s\.?)",
    "CJA": r"(?P<CJA>Code\sde\sjustice\sadministrative|CJA)",
}

CODE_REFERENCE = {
    "CCIV": "Code civil",
    "CPRCIV": "Code de procédure civile",
    "CCOM": "Code de commerce",
    "CTRAV": "Code du travail",
    "CPI": "Code de la propriété intellectuelle",
    "CPEN": "Code pénal",
    "CPP": "Code de procédure pénale",
    "CASSUR": "Code des assurances",
    "CCONSO": "Code de la consommation",
    "CSI": "Code de la sécurité intérieure",
    "CSP": "Code de la santé publique",
    "CSS": "Code de la sécurité sociale",
    "CESEDA": "Code de l'entrée et du séjour des étrangers et du droit d'asile",
    "CGCT": "Code général des collectivités territoriales",
    "CPCE": "Code des postes et des communications électroniques",
    "CENV": "Code de l'environnement",
    "CJA": "Code de justice administrative",
}

def get_long_and_short_code(code_name):
    '''
    Accéder aux deux versions du nom du code: le nom complet et son abréviation

    Arguments: 
        code_name: le nom du code (version longue ou courte)
    Returns:
        long_code: le nom complet du code
        short_code: l'abréviation du code
    Raises:
        Si le nom du code n'a pas été trouvé les valeurs sont nulles (None, None)
    '''
    
    if code_name in MAIN_CODELIST.keys():
        short_code = code_name
        long_code = MAIN_CODELIST[code_name]
    elif code_name in MAIN_CODELIST.values():
        long_code = code_name
        short_code_results = [k for k, v in MAIN_CODELIST.items() if v == code_name]
        if len(short_code_results) > 0:
            short_code = short_code_results[0]
        else: 
            short_code = None
    else:
        short_code, long_code = None, None
    return(long_code, short_code)


def get_code_full_name_from_short_code(short_code):
    """
    Shortcut to get corresponding full_name from short_code

    Arguments:
        short_code: short form of Code eg. CCIV
    Returns:
        full_name: long form of code eg. Code Civil
    """
    try:
        return MAIN_CODELIST[short_code]
    except ValueError:
        return None


def get_short_code_from_full_name(full_name):
    """
    Shortcut to get corresponding short_code from full_name

    Arguments:
        full_name: long form of code eg. Code Civil
    Returns:
        short_code: short form of Code eg. CCIV
    """
    keys = [k for k, v in MAIN_CODELIST.items() if v == full_name]
    if len(keys) > 0:
        return keys[0]
    else:
        return None

    
def filter_code_regex(short_code_list):
    """
    Filter codes to match in document
    Arguments:
        code_list: [short_code, ...]
    Returns:
        regex: string
    """
    short_code_list = sorted(short_code_list)
    if len(short_code_list) == 0:
        return "({})".format("|".join(list(CODE_REGEX.values())))
    elif len(short_code_list) == 1:
        return CODE_REGEX[short_code_list[0]]
    else:
        selected_code_dict = [CODE_REGEX[x] for x in short_code_list] 
        return "({})".format("|".join(selected_code_dict))

def filter_code_reference(short_code_list):
    """
    Filter code reference given a code_list 
    Arguments:
        code_list: [short_code, ...]
    Returns:
        filter_code_reference: selected CODE REFERENCE
    """
    if len(short_code_list)== 0:
        return CODE_REFERENCE
    return {x: CODE_REFERENCE[x] for x in sorted(short_code_list)}

class TestCodeFormats:
    @pytest.mark.parametrize("input", list(CODE_REFERENCE.keys()))
    def test_short2long_code(self, input):
        
        assert get_code_full_name_from_short_code(input) == CODE_REFERENCE[input], (
            input,
            CODE_REFERENCE[input],
        )

    @pytest.mark.parametrize("input", list(CODE_REFERENCE.values()))
    def test_long2short_code(self, input):
        print(input)
        result = get_short_code_from_full_name(input)
        expected = [k for k,v in CODE_REFERENCE.items() if v == input][0]
        assert result == expected, (result, expected)

    @pytest.mark.parametrize("input", list(CODE_REFERENCE.keys()))
    def test_get_long_and_short_code(self, input):
        result = get_long_and_short_code(input)
        expected = (CODE_REFERENCE[input], input)
        assert expected == result, result
        
        
class TestFilterCode:
    def test_code_regex_match_code_ref(self):
        assert set(CODE_REFERENCE) - set(CODE_REGEX) == set()
    
    def test_filter_regex_empty(self):
        result = filter_code_regex([])
        expected = "({})".format("|".join(list(CODE_REGEX.values())))
        assert result == expected, result
    
    def test_filter_regex_unique(self):
        result = filter_code_regex(["CJA"])
        expected = CODE_REGEX["CJA"]
        assert result == expected, (result, expected)
    
    def test_filter_code_regex_manual(self):
        code_list = sorted(["CJA", "CPP", "CCIV"])
        result = filter_code_regex(code_list)
        expected = "({})".format("|".join([CODE_REGEX[x] for x in code_list]))
        assert result == expected, (result, expected)
    
    def test_filter_code_regex_random(self):
        random_code_list = sorted(random.choices(list(CODE_REFERENCE), k=5))
        result = filter_code_regex(random_code_list)
        expected = "({})".format("|".join([CODE_REGEX[c] for c in random_code_list]))
        assert result == expected, result
    
    def test_filter_reference_empty(self):
        result = filter_code_reference([])
        assert result == CODE_REFERENCE
    
    def test_filter_reference_single(self):
        result = filter_code_reference(["CPP"])
        assert result == {"CPP": CODE_REFERENCE['CPP']}
    
    def test_filter_reference_manual(self):
        code_list = sorted(["CPP", "CPEN", "CENV"])
        result = filter_code_reference(code_list)
        expected = {x: CODE_REFERENCE[x] for x in code_list}
        assert result == expected, result
    
    def test_filter_reference_random(self):
        random_code_list = sorted(random.choices(list(CODE_REFERENCE), k=5))
        result = filter_code_reference(random_code_list)
        expected = {k: CODE_REFERENCE[k] for k in random_code_list}
        assert result == expected, result