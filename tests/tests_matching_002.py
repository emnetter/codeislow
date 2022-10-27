
import re

ARTICLE_REGEX = "(?P<art>((A|a)rticles?|(A|a)rt\.))"
CODE_DICT  = {
    "CCIV": "(?P<CCIV>du?\sCode civil|C\.\sciv\.|Code\sciv\.)",
    "CPRCIV": "(?P<CPRCIV>du\sCode\sde\sprocédure civile|C\.\spr\.\sciv\.|CPC|du\sCPC)",
    "CCOM": "(?P<CCOM>du\nCode\sde\scommerce|C\.\scom\.)",
    "CTRAV": "(?P<CTRAV>du\sCode\sdu\stravail|C\.\strav\.)",
    "CPI": "(?P<CPI>du\sCode\sde\sla\spropriété\sintellectuelle|CPI|C\.\spr\.\sint\.|du\sCPI)",
    "CPEN": "(?P<CPEN>du\sCode\spénal|C\.\spén\.)",
    "CPP": "(?P<CPP>du\sCode\sde\sprocédure\spénale|du CPP|CPP)",
    "CASSU": "(?P<CASSUR>du\sCode\sdes\sassurances|C\.\sassur\.)",
    "CCONSO": "(?P<CCONSO>du\sCode\sde\sla\sconsommation|C\.\sconso\.)",
    "CSI": "(?P<CSI>du\sCode\sde\slasécurité intérieure|CSI|du CSI)",
    "CSP": "(?P<CSP>du\sCode\sde\slasanté publique|C\.\ssant\.\spub\.|CSP|du CSP)",
    "CSS": "(?P<CSS>du\sCode\sde\slasécurité sociale|C\.\ssec\.\ssoc\.|CSS|du CSS)",
    "CESEDA": "(?P<CESEDA>du\nCode\sde\sl'entrée\set\sdu\sséjour\sdes\sétrangers\set\sdu\sdroit\sd'asile|CESEDA|du\sCESEDA)",
    "CGCT": "(?P<CGCT>du\sCode\sgénéral\sdes\scollectivités\sterritoriales|CGCT|du CGCT)",
    "CPCE": "(?P<CPCE>du\sCode\sdes\spostes\set\sdes\scommunications\sélectroniques|CPCE|du\sCPCE)",
    "CENV": "(?P<CENV>du\nCode\sde\sl'environnement|C.\senvir.|\sCE(\s|\.)|\sdu\sCE)",
    "CJA": "(?P<CJA>du\nCode\sde\sjustice\sadministrative|CJA|du\sCJA)",
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