#!/usr/bin/env python3
#filename: matching.py
"""
The matching module

Ce module permet la detection des articles du code de droit français

"""

import re

from parsing import parse_doc
from code_references import filter_code_regex, CODE_REFERENCE, CODE_REGEX

ARTICLE_REGEX = r"(?P<art>(Articles?|Art\.))"

# ARTICLE_REF = re.compile("\d+")
# ARTICLE_ID = r"(L|R|A|D)?(\.|\s)?\d+(-\d+)?((\s(al\.|alinea)?\s\d+)?(\s|\.)"




def switch_pattern(selected_codes=None, pattern="article_code"):
    """
    Build pattern recognition using pattern short code switch

    Arguments
    ---------
    selected_codes: array
        a list of short codes to select. Default to None
    pattern: str
        a string article_code or code_article. Default to article_code
    Returns
    ---------
    regex_pattern: str
        a compiled regex pattern
    Raise
    --------
    ValueError: 
        pattern name is wrong
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
    """
    Une fonction qui renvoie un dictionnaire de resultats: trié par code (version abbréviée) avec la liste des articles détectés lui appartenant. 

    Arguments
    ----------
    full_text: str
        a string of the full document normalized
    pattern_format: str
        a string representing the pattern format article_code or code_article. Defaut to article_code

    Returns
    ----------
    code_found: dict
        a dict compose of short version of code as key and list of the detected articles references  as values {code: [art_ref, art_ref2, ... ]}
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
    Renvoie les références des articles détectés dans le texte

    Arguments
    -----------
    full_text: str
        a string of the full document normalized
    selected_shortcodes: array
        a list of selected codes in short format for filtering article detection. Default is an empty list (which stands for no filter) 
    pattern_format: str
    a string representing the pattern format article_code or code_article. Defaut to article_code

    Yields
    --------
    code_short_name:str

    article_number:str
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