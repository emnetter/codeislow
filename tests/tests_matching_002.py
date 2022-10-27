import logging
import re
from test_parsing_001 import parse_doc

logging.basicConfig(filename='matching.log', encoding='utf-8', level=logging.DEBUG)

ARTICLE_REGEX = r"(?P<art>((A|a)rticles?|(A|a)rt\.))"
CODE_DICT  = {
    "CCIV": r"(?P<CCIV>du?\sCode civil|C\.\sciv\.|Code\sciv\.)",
    "CPRCIV": r"(?P<CPRCIV>du\sCode\sde\sprocédure civile|C\.\spr\.\sciv\.|CPC|du\sCPC)",
    "CCOM": r"(?P<CCOM>du\nCode\sde\scommerce|C\.\scom\.)",
    "CTRAV": r"(?P<CTRAV>du\sCode\sdu\stravail|C\.\strav\.)",
    "CPI": r"(?P<CPI>du\sCode\sde\sla\spropriété\sintellectuelle|CPI|C\.\spr\.\sint\.|du\sCPI)",
    "CPEN": r"(?P<CPEN>du\sCode\spénal|C\.\spén\.)",
    "CPP": r"(?P<CPP>du\sCode\sde\sprocédure\spénale|du CPP|CPP)",
    "CASSU": r"(?P<CASSUR>du\sCode\sdes\sassurances|C\.\sassur\.)",
    "CCONSO": r"(?P<CCONSO>du\sCode\sde\sla\sconsommation|C\.\sconso\.)",
    "CSI": r"(?P<CSI>du\sCode\sde\slasécurité intérieure|CSI|du CSI)",
    "CSP": r"(?P<CSP>du\sCode\sde\slasanté publique|C\.\ssant\.\spub\.|CSP|du CSP)",
    "CSS": r"(?P<CSS>du\sCode\sde\slasécurité sociale|C\.\ssec\.\ssoc\.|CSS|du CSS)",
    "CESEDA": r"(?P<CESEDA>du\nCode\sde\sl'entrée\set\sdu\sséjour\sdes\sétrangers\set\sdu\sdroit\sd'asile|CESEDA|du\sCESEDA)",
    "CGCT": r"(?P<CGCT>du\sCode\sgénéral\sdes\scollectivités\sterritoriales|CGCT|du CGCT)",
    "CPCE": r"(?P<CPCE>du\sCode\sdes\spostes\set\sdes\scommunications\sélectroniques|CPCE|du\sCPCE)",
    "CENV": r"(?P<CENV>du\nCode\sde\sl'environnement|C.\senvir.|\sCE(\s|\.)|\sdu\sCE)",
    "CJA": r"(?P<CJA>du\nCode\sde\sjustice\sadministrative|CJA|du\sCJA)",
}

CODE_REGEX = "|".join(CODE_DICT.values())
# ARTICLE_REF = re.compile("\d+")
# ARTICLE_ID = re.compile("?((L|R)?(\.))(\d+)?(-\d+)?(\s(al\.|alinea)\s\d+)")

# JURI_PATTERN = re.compile(ARTICLE_P, flags=re.I)


def switch_pattern(pattern="article_code"):
    """
    Build pattern recognition

    Arguments:
        pattern: a string article_code or code_article 

    Raise:
        ValueError: pattern name is wrong
    """

    if fmt not in ["article_code", "code_article"]:
        raise ValueError("Wrong pattern name: choose between 'article_code' or 'code_article'")
    if fmt == "article_code":
        return re.compile(f"{ARTICLE_REGEX}(?P<ref>.*?)({CODE_REGEX}$)", flags=re.I)
    else:
        return re.compile(f"({CODE_REGEX}){ARTICLE_REGEX}(?P<ref>.*?)$)", flags=re.I)


def match_code_and_articles(full_text, pattern_format="article_code"):
    """"
    Detect law articles of supported codes 
    
    Arguments:
        full_text: a string of the full document normalized
        pattern_format: a string representing the pattern format article_code or code_article. Defaut to article_code

    Returns:
        results_dict: a dict compose of short version of code as key and list of the detected articles references  as values {code: [art_ref, art_ref2, ... ]}
    """
    article_pattern = switch_pattern(pattern_format)
    code_found = {}
    full_text = re.sub(r"\r|\n|\t", " ", "".join(full_text))
    for i, match in enumerate(re.finditer(article_pattern, full_text)):
        needle = match.groupdict()
        qualified_needle = {key: value for key, value in needle.items() if value is not None}
        print(i+1, qualified_needle)
        ref = match.group("ref").strip()
        refs = [n for n in re.split(r"(\set\s|,\s)", ref) if n not in [" et ", ", "]]
        code = [k for k in qualified_needle.keys() if k not in ["ref", "art"]][0]
        if code not in code_found:
            code_found[code] = refs
        else:
            code_found[code].extend(refs)
    return code_found


    class TestMatching:
        def test_full_text_normalization(self):
            file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf"]
            for file_path in file_paths:
                abspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_path)
                logging.debug(f'[LOAD] filename: {abspath}')
                full_text = parse_doc(abspath)
                logging.debug(f'[PARSE] filename: {abspath} - found {len(full_text)} sentences')
                match_code_and_articles(full_text)