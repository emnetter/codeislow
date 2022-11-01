import logging
import os
import re
import pytest

from parsing import parse_doc
from requesting import MAIN_CODELIST

# logging.basicConfig(filename="matching.log", encoding="utf-8", level=logging.DEBUG)

ARTICLE_REGEX = r"(?P<art>(Articles?|Art\.))"
CODE_DICT = {
    "CCIV": r"(?P<CCIV>Code civil|C\.\sciv\.|Code\sciv\.|C\.civ\.|civ\.|CCIV)",
    "CPRCIV": r"(?P<CPRCIV>Code\sde\sprocédure civile|C\.\spr\.\sciv\.|CPC)",
    "CCOM": r"(?P<CCOM>Code\sde\scommerce|C\.\scom\.)",
    "CTRAV": r"(?P<CTRAV>Code\sdu\stravail|C\.\strav\.)",
    "CPI": r"(?P<CPI>Code\sde\sla\spropriété\sintellectuelle|CPI|C\.\spr\.\sint\.)",
    "CPEN": r"(?P<CPEN>Code\spénal|C\.\spén\.)",
    "CPP": r"(?P<CPP>Code\sde\sprocédure\spénale|CPP)",
    "CASSU": r"(?P<CASSUR>Code\sdes\sassurances|C\.\sassur\.)",
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

CODE_REGEX = "|".join(CODE_DICT.values())
# ARTICLE_REF = re.compile("\d+")
# ARTICLE_ID = re.compile("?((L|R|A|D)?(\.))(\d+)?(-\d+)?(\s(al\.|alinea)\s\d+)")


def switch_pattern(pattern="article_code"):
    """
    Build pattern recognition using pattern short code switch

    Arguments:
        pattern: a string article_code or code_article

    Returns:
        regex_pattern: compiled regex pattern
    Raise:
        ValueError: pattern name is wrong
    """

    if pattern not in ["article_code", "code_article"]:
        raise ValueError(
            "Wrong pattern name: choose between 'article_code' or 'code_article'"
        )
    if pattern == "article_code":
        return re.compile(f"{ARTICLE_REGEX}(?P<ref>.*?)({CODE_REGEX})", flags=re.I)
    else:
        return re.compile(f"({CODE_REGEX}){ARTICLE_REGEX}(?P<ref>.*?)$)", flags=re.I)


def match_code_and_articles(full_text, pattern_format="article_code"):
    """ "
    Detect law articles of supported codes

    Arguments:
        full_text: a string of the full document normalized
        pattern_format: a string representing the pattern format article_code or code_article. Defaut to article_code

    Returns:
        code_found: a dict compose of short version of code as key and list of the detected articles references  as values {code: [art_ref, art_ref2, ... ]}
    """
    article_pattern = switch_pattern(pattern_format)
    code_found = {}

    # normalisation
    full_text = re.sub(r"\r|\n|\t|\xa0", " ", " ".join(full_text))
    for i, match in enumerate(re.finditer(article_pattern, full_text)):
        needle = match.groupdict()
        qualified_needle = {
            key: value for key, value in needle.items() if value is not None
        }
        msg = f"#{i+1}\t{qualified_needle}"
        # logging.debug(msg)
        # get the code shortname based on regex group name <code>
        code = [k for k in qualified_needle.keys() if k not in ["ref", "art"]][0]

        ref = match.group("ref").strip()
        # split multiple articles of a same code
        refs = [
            n
            for n in re.split(r"(\set\s|,\s|\sdu)", ref)
            if n not in [" et ", ", ", " du", " ", ""]
        ]
        # normalize articles to remove dots, spaces, caret and 'alinea'
        refs = [
            "-".join(
                [
                    r
                    for r in re.split(r"\s|\.|-", ref)
                    if r not in [" ", "", "al", "alinea", "alinéa"]
                ]
            )
            for ref in refs
        ]
        # clean caracters for everything but numbers and (L|A|R|D) and caret
        normalized_refs = []
        for ref in refs:
            # accepted caracters for article
            ref = "".join(
                [n for n in ref if (n.isdigit() or n in ["L", "A", "R", "D", "-"])]
            )
            if ref.endswith("-"):
                ref = ref[:-1]
            # remove caret separating article nb between first letter
            special_ref = ref.split("-", 1)
            if special_ref[0] in ["L", "A", "R", "D"]:
                normalized_refs.append("".join(special_ref))
            else:
                normalized_refs.append(ref)

        if code not in code_found:
            # append article references
            code_found[code] = normalized_refs
        else:
            # append article references to existing list
            code_found[code].extend(normalized_refs)

    return code_found

def gen_matching_results(full_text, pattern_format="article_code"):
    """ "
    Detect law articles of supported codes

    Arguments:
        full_text: a string of the full document normalized
        pattern_format: a string representing the pattern format article_code or code_article. Defaut to article_code

    Yield:
        code_short_name
        code_long_name
        article
    """
    article_pattern = switch_pattern(pattern_format)
    code_found = {}

    # normalisation
    full_text = re.sub(r"\r|\n|\t|\xa0", " ", " ".join(full_text))
    for i, match in enumerate(re.finditer(article_pattern, full_text)):
        needle = match.groupdict()
        qualified_needle = {
            key: value for key, value in needle.items() if value is not None
        }
        msg = f"#{i+1}\t{qualified_needle}"
        # logging.debug(msg)
        # get the code shortname based on regex group name <code>
        code = [k for k in qualified_needle.keys() if k not in ["ref", "art"]][0]

        ref = match.group("ref").strip()
        # split multiple articles of a same code
        refs = [
            n
            for n in re.split(r"(\set\s|,\s|\sdu)", ref)
            if n not in [" et ", ", ", " du", " ", ""]
        ]
        # normalize articles to remove dots, spaces, caret and 'alinea'
        refs = [
            "-".join(
                [
                    r
                    for r in re.split(r"\s|\.|-", ref)
                    if r not in [" ", "", "al", "alinea", "alinéa"]
                ]
            )
            for ref in refs
        ]
        # clean caracters for everything but numbers and (L|A|R|D) and caret
        normalized_refs = []
        for ref in refs:
            # accepted caracters for article
            ref = "".join(
                [n for n in ref if (n.isdigit() or n in ["L", "A", "R", "D", "-"])]
            )
            if ref.endswith("-"):
                ref = ref[:-1]
            # remove caret separating article nb between first letter
            special_ref = ref.split("-", 1)
            if special_ref[0] in ["L", "A", "R", "D"]:
                # normalized_refs.append("".join(special_ref))
                yield(code, MAIN_CODELIST[code], "".join(special_ref))
            else:
                # normalized_refs.append(ref)
                yield(code, MAIN_CODELIST[code], ref)

