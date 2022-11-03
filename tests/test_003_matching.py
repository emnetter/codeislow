import os
import re
import pytest

from test_001_parsing import parse_doc
from test_002_code_references import filter_code_regex, CODE_REFERENCE

ARTICLE_REGEX = r"(?P<art>(Articles?|Art\.))"

# ARTICLE_REF = re.compile("\d+")
# ARTICLE_ID = r"(L|R|A|D)?(\.|\s)?\d+(-\d+)?((\s(al\.|alinea)?\s\d+)?(\s|\.)"




def switch_pattern(selected_codes=None, pattern="article_code"):
    """
    Build pattern recognition using pattern short code switch

    Arguments:
        selected_codes: a list of short codes to select. Default to None
        pattern: a string article_code or code_article. Default to article_code
    Returns:
        regex_pattern: compiled regex pattern
    Raise:
        ValueError: pattern name is wrong
    """

    code_regex = filter_code_regex(selected_codes)

    if pattern not in ["article_code", "code_article"]:
        raise ValueError(
            "Wrong pattern name: choose between 'article_code' or 'code_article'"
        )
    if pattern == "article_code":
        return re.compile(f"{ARTICLE_REGEX}(?P<ref>.*?){code_regex}", flags=re.I)
    # else:
    #     #code_article
    #     # return re.compile(f"{code_regex}.*?{ARTICLE_REGEX}(\s|\.)(?P<ref>.*?)(\.|\s)", flags=re.I)
    #     return re.compile(f"{code_regex}.*?{ARTICLE_REGEX}.*?{ARTICLE_ID}", flags=re.I)

def get_matching_results_dict(full_text, selected_short_codes=[], pattern_format="article_code"):
    """ "
    Une fonction qui revoie un dictionnaire de resultats: trié par code (version abbréviée) avec la liste des articles détectés lui appartenant. 

    Arguments:
        full_text: a string of the full document normalized
        pattern_format: a string representing the pattern format article_code or code_article. Defaut to article_code

    Returns:
        code_found: a dict compose of short version of code as key and list of the detected articles references  as values {code: [art_ref, art_ref2, ... ]}
    """
    article_pattern = switch_pattern(selected_short_codes, pattern_format)
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

def get_matching_result_item(full_text, selected_shortcodes=[], pattern_format="article_code"):
    """"
    Générateur: renvoie la référence de l'article détecté dans le texte

    Arguments:
        full_text: a string of the full document normalized
        selected_shortcodes: a list of selected codes in short format for filtering article detection. Default is an empty list (which stands for no filter) 
        pattern_format: a string representing the pattern format article_code or code_article. Defaut to article_code

    Yield:
        (code_short_name:str, article_number:str)
    """
    article_pattern = switch_pattern(selected_shortcodes, pattern_format)
    # normalisation des espaces dans le texte
    full_text = re.sub(r"\r|\n|\t|\f|\xa0", " ", " ".join(full_text))
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
        # split multiple articles of a same code example: Article 22, 23 et 24 du Code
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
        for ref in refs:
            # accepted caracters for article
            # exemple: 1224 du => Non 298 al 32 => Non R-288 => oui A-24-14=> oui
            ref = "".join(
                [n for n in ref if (n.isdigit() or n in ["L", "A", "R", "D", "-"])]
            )
            if ref.endswith("-"):
                ref = ref[:-1]
            # remove caret separating article nb between first letter
            # exemple: L-248-1 = > L248-1
            special_ref = ref.split("-", 1)
            if special_ref[0] in ["L", "A", "R", "D"]:
                yield(code, "".join(special_ref))
                
            else:
                yield(code, ref)

class TestMatching:
    def test_matching_result_dict_codes_no_filter_pattern_article_code(self):
        file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            full_text = parse_doc(abspath)
            results_dict = get_matching_results_dict(full_text,None, "article_code")
            code_list = list(results_dict.keys())
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
            articles_detected = [
                item for sublist in results_dict.values() for item in sublist
            ]
            assert len(articles_detected) == 37, len(articles_detected)
            assert results_dict["CCIV"] == [
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
            ], results_dict["CCIV"]
            assert results_dict["CPRCIV"] == ["1038", "1289-2"], results_dict["CPRCIV"]
            assert results_dict["CASSUR"] == ["L385-2", "R343-4", "A421-13"], results_dict[
                "CASSUR"
            ]
            assert results_dict["CCOM"] == ["L611-2"], results_dict["CCOM"]
            assert results_dict["CTRAV"] == ["L1111-1"], results_dict["CTRAV"]
            assert results_dict["CPI"] == ["L112-1", "L331-4"], results_dict["CPI"]
            assert results_dict["CPEN"] == ["131-4", "225-7-1"], results_dict["CPEN"]
            assert results_dict["CPP"] == ["694-4-1", "R57-6-1"], results_dict["CPP"]
            assert results_dict["CCONSO"] == ["L121-14", "R742-52"], results_dict["CCONSO"]
            assert results_dict["CSI"] == ["L622-7", "R314-7"], results_dict["CSI"]
            assert results_dict["CSS"] == ["L173-8"], results_dict["CSS"]
            assert results_dict["CSP"] == ["L1110-1"], results_dict["CSP"]
            assert results_dict["CENV"] == ["L124-1"], ("CENV", results_dict["CENV"])
            assert results_dict["CJA"] == ["L121-2"], ("CJA", results_dict["CJA"])
            assert results_dict["CGCT"] == ["L1424-71", "L1"], ("CGCT", results_dict["CGCT"])
            assert results_dict["CESEDA"] == ["L753-1", "12"], ("CESEDA", results_dict["CESEDA"])
    
    def test_matching_result_dict_codes_filter_pattern_article_code(self):
        selected_codes = ["CASSUR", "CENV", "CSI", "CCIV"]
        file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            full_text = parse_doc(abspath)
            results_dict = get_matching_results_dict(full_text,selected_codes, "article_code")
            code_list = list(results_dict.keys())
            assert len(code_list) == len(selected_codes), len(code_list)
            assert sorted(code_list) == [
                "CASSUR",
                "CCIV",
                "CENV",
                "CSI",
            ], sorted(code_list)
            # articles_detected = [
                # item for sublist in results_dict.values() for item in sublist
            # ]
            # assert len(articles_detected) == 37, len(articles_detected)
            assert results_dict["CCIV"] == [
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
            ], results_dict["CCIV"]
            # assert results_dict["CASSUR"] == ["L385-2", "R343-4", "A421-13"], results_dict[
            #     "CASSUR"
            # ]
            # assert results_dict["CSI"] == ["L622-7", "R314-7"], results_dict["CSI"]
            assert results_dict["CENV"] == ["L124-1"], ("CENV", results_dict["CENV"])
            
    