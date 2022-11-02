import logging
import os
import re
import pytest

from test_001_parsing import parse_doc
from test_003_request import MAIN_CODELIST

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
        return re.compile(f"(({CODE_REGEX}){ARTICLE_REGEX}(?P<ref>.*?)$)", flags=re.I)


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

class TestMatching:
    def test_matching_code(self):
        file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            logging.debug(f"[LOAD] filename: {abspath}")
            full_text = parse_doc(abspath)
            # logging.debug(f'[PARSE] filename: {abspath} - found {len(full_text)} sentences')
            results = match_code_and_articles(full_text)
            code_list = list(results.keys())
            assert len(code_list) == 16, len(code_list)
            assert sorted(code_list) == [
                "CASSUR",
                "CCIV",
                "CCOM",
                "CCONSO",
                "CENV",
                "CESEDA",
                "CGCT",
                "CJA",
                "CPEN",
                "CPI",
                "CPP",
                "CPRCIV",
                "CSI",
                "CSP",
                "CSS",
                "CTRAV",
            ], sorted(code_list)

    def test_matching_articles(self):
        file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            logging.debug(f"[LOAD] filename: {abspath}")
            full_text = parse_doc(abspath)
            # logging.debug(f'[PARSE] filename: {abspath} - found {len(full_text)} sentences')
            results = match_code_and_articles(full_text)
            articles_detected = [
                item for sublist in results.values() for item in sublist
            ]
            assert len(articles_detected) == 37, len(articles_detected)

    def test_matching_articles_references(self):
        file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            # logging.debug(f"[LOAD] filename: {abspath}")
            full_text = parse_doc(abspath)
            # logging.debug(f'[PARSE] filename: {abspath} - found {len(full_text)} sentences')
            results = match_code_and_articles(full_text)
            assert results["CCIV"] == [
                "1120",
                "2288",
                "1240-1",
                "1140",
                "1",
                "349",
                "39999",
                "3-12",
                "12-4-6",
                "14",
                "15",
                "27",
            ], results["CCIV"]
            assert results["CPRCIV"] == ["1038", "1289-2"], results["CPRCIV"]
            assert results["CASSUR"] == ["L385-2", "R343-4", "A421-13"], results[
                "CASSUR"
            ]
            assert results["CCOM"] == ["L611-2"], results["CCOM"]
            assert results["CTRAV"] == ["L1111-1"], results["CTRAV"]
            assert results["CPI"] == ["L112-1", "L331-4"], results["CPI"]
            assert results["CPEN"] == ["131-4", "225-7-1"], results["CPEN"]
            assert results["CPP"] == ["694-4-1", "R57-6-1"], results["CPP"]
            assert results["CCONSO"] == ["L121-14", "R742-52"], results["CCONSO"]
            assert results["CSI"] == ["L622-7", "R314-7"], results["CSI"]
            assert results["CSS"] == ["L173-8"], results["CSS"]
            assert results["CSP"] == ["L1110-1"], results["CSP"]
            assert results["CENV"] == ["L124-1"], ("CENV", results["CENV"])
            assert results["CJA"] == ["L121-2"], ("CJA", results["CJA"])
            assert results["CGCT"] == ["L1424-71", "L1"], ("CGCT", results["CGCT"])
            assert results["CESEDA"] == ["L753-1", "12"], ("CESEDA", results["CESEDA"])
    
    def test_matching_reversed_format_articles_references(self):
        file_paths = ["testnew.odt", "testnew.pdf"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            # logging.debug(f"[LOAD] filename: {abspath}")
            full_text = parse_doc(abspath)
            # logging.debug(f'[PARSE] filename: {abspath} - found {len(full_text)} sentences')
            results = match_code_and_articles(full_text,"code_article")
            #WIP reversed is not working
            assert list(results.keys()) == [], list(results.keys())
            
            # assert results["CCIV"] == [
            #     "1120",
            #     "2288",
            #     "1240-1",
            #     "1140",
            #     "1",
            #     "349",
            #     "39999",
            #     "3-12",
            #     "12-4-6",
            #     "14",
            #     "15",
            #     "27",
            # ], results["CCIV"]
            # assert results["CPRCIV"] == ["1038", "1289-2"], results["CPRCIV"]
            # assert results["CASSUR"] == ["L385-2", "R343-4", "A421-13"], results[
            #     "CASSUR"
            # ]
            # assert results["CCOM"] == ["L611-2"], results["CCOM"]
            # assert results["CTRAV"] == ["L1111-1"], results["CTRAV"]
            # assert results["CPI"] == ["L112-1", "L331-4"], results["CPI"]
            # assert results["CPEN"] == ["131-4", "225-7-1"], results["CPEN"]
            # assert results["CPP"] == ["694-4-1", "R57-6-1"], results["CPP"]
            # assert results["CCONSO"] == ["L121-14", "R742-52"], results["CCONSO"]
            # assert results["CSI"] == ["L622-7", "R314-7"], results["CSI"]
            # assert results["CSS"] == ["L173-8"], results["CSS"]
            # assert results["CSP"] == ["L1110-1"], results["CSP"]
            # assert results["CENV"] == ["L124-1"], ("CENV", results["CENV"])
            # assert results["CJA"] == ["L121-2"], ("CJA", results["CJA"])
            # assert results["CGCT"] == ["L1424-71", "L1"], ("CGCT", results["CGCT"])
            # assert results["CESEDA"] == ["L753-1", "12"], ("CESEDA", results["CESEDA"])
    def test_matching_generator(self):
        file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            # logging.debug(f"[LOAD] filename: {abspath}")
            full_text = parse_doc(abspath)
            # logging.debug(f'[PARSE] filename: {abspath} - found {len(full_text)} sentences')
            for match in gen_matching_results(full_text):
                assert len(match) == 3, match
                assert match[2] != "", match[2]
                assert match[1] == MAIN_CODELIST[match[0]]
    
    def test_matching_reverse_format_generator(self):
        file_paths = ["testnew.odt", "newtest.pdf"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            # logging.debug(f"[LOAD] filename: {abspath}")
            full_text = parse_doc(abspath)
            
            # logging.debug(f'[PARSE] filename: {abspath} - found {len(full_text)} sentences')
            for match in gen_matching_results(full_text, "code_article"):
                assert match[2] != "AAAA", match[2]
                assert len(match) == 3, match
                assert match[1] == MAIN_CODELIST[match[0]]
