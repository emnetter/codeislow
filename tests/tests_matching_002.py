
import re

ARTICLE_REGEX = "(?P<art>((A|a)rticles?|(A|a)rt\.))"
CODE_DICT  = {
    "CCIV": "(?P<CCIV>du Code civil|C\.\sciv\.|civ\.)",
    "CPRCIV": "(?P<CPRCIV>du Code de procédure civile|C\. pr\. civ\.|CPC|du CPC)",
    "CCOM": "(?P<CCOM>du Code de commerce|C\. com\.)",
    "CTRAV": "(?P<CTRAV>du Code du travail|C\. trav\.)",
    "CPI": "(?P<CPI>du Code de la propriété intellectuelle|CPI|C\. pr\. int\.|du CPI)",
    "CPEN": "(?P<CPEN>du Code pénal|C\. pén\.)",
    "CPP": "(?P<CPP>du Code de procédure pénale|du CPP|CPP)",
    "CASSU": "(?P<CASSUR>du Code des assurances|C\. assur\.)",
    "CCONSO": "(?P<CCONSO>du Code de la consommation|C\. conso\.)",
    "CSI": "(?P<CSI>du Code de la sécurité intérieure|CSI|du CSI)",
    "CSP": "(?P<CSP>du Code de la santé publique|C\.\ssant\. pub\.|CSP|du CSP)",
    "CSS": "(?P<CSS>du Code de la sécurité sociale|C\.\ssec\.\ssoc\.|CSS|du CSS)",
    "CESEDA": "(?P<CESEDA>du Code de l'entrée et du séjour des étrangers et du droit d'asile|CESEDA|du CESEDA)",
    "CGCT": "(?P<CGCT>du Code général des collectivités territoriales|CGCT|du CGCT)",
    "CPCE": "(?P<CPCE>du Code des postes et des communications électroniques|CPCE|du CPCE)",
    #Trop large CE
    "CENV": "(?P<CENV>du Code de l'environnement|C. envir.|\sCE(\s|\.)|\sdu CE)",
    "CJA": "(?P<CJA>du Code de justice administrative|CJA|du CJA)",
}

CODE_REGEX = "|".join(CODE_DICT.values())
# ARTICLE_ID = re.compile("?((L|R)?(\.))(\d+)?(-\d+)?(\s(al\.|alinea)\s\d+)")

JURI_PATTERN = re.compile(ARTICLE_P, flags=re.I)


def switch_pattern(fmt="code_article"):
    if fmt == "code_article":
        return re.compile(f"{ARTICLE_REGEX}(?P<ref>.*?)({CODE_REGEX}$)")
    else:
        return re.compile(f"({CODE_REGEX}){ARTICLE_REGEX}(?P<ref>.*?)$)")


def match_code_and_articles():
    code_found = {}
    full_text = re.sub("\r|\n|\t", " ", "".join(full_text))
    for i, match in enumerate(re.finditer(JURI_PATTERN, full_text)):
        needle = match.groupdict()
        qualified_needle = {key: value for key, value in needle.items() if value is not None}
        print(i+1, qualified_needle)
        ref = match.group("ref").strip()
        refs = [n for n in re.split("(\set\s|,\s)", ref) if n not in [" et ", ", "]]
        code = [k for k in qualified_needle.keys() if k not in ["ref", "art"]][0]
        if code not in code_found:
            code_found[code] = refs
        else:
            code_found[code].extend(refs)
    return code_found