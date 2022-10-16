#coding: utf-8

import os
import re

import docx
from PyPDF2 import PdfReader
from odf import text, teletype
from odf.opendocument import load
    
# ARTICLE_REGEX = "(?P<art>(A|a)rt(\.|ticle))"
ARTICLE_REGEX = "(?P<art>((A|a)rticles?|(A|a)rt\.))"
CODE_DICT  = {
    "CCIV": "(?P<CCIV>du Code civil|C\. civ\.|civ\.)",
    "CPRCIV": "(?P<CPRCIV>du Code de procédure civile|C\. pr\. civ\.|CPC|du CPC)",
    "CCOM": "(?P<CCOM>du Code de commerce|C\. com\.)",
    "CTRAV": "(?P<CTRAV>du Code du travail|C\. trav\.)",
    "CPI": "(?P<CPI>du Code de la propriété intellectuelle|CPI|C\. pr\. int\.|du CPI)",
    "CPEN": "(?P<CPEN>du Code pénal|C\. pén\.)",
    "CPP": "(?P<CPP>du Code de procédure pénale|du CPP|CPP)",
    "CASSU": "(?P<CASSUR>du Code des assurances|C\. assur\.)",
    "CCONSO": "(?P<CCONSO>du Code de la consommation|C\. conso\.)",
    "CSI": "(?P<CSI>du Code de la sécurité intérieure|CSI|du CSI)",
    "CSP": "(?P<CSP>du Code de la santé publique|C\. sant\. pub\.|CSP|du CSP)",
    "CSS": "(?P<CSS>du Code de la sécurité sociale|C\. sec\. soc\.|CSS|du CSS)",
    "CESEDA": "(?P<CESEDA>du Code de l'entrée et du séjour des étrangers et du droit d'asile|CESEDA|du CESEDA)",
    "CGCT": "(?P<CGCT>du Code général des collectivités territoriales|CGCT|du CGCT)",
    "CPCE": "(?P<CPCE>du Code des postes et des communications électroniques|CPCE|du CPCE)",
    "CENV": "(?P<CENV>du Code de l'environnement|C. envir.|CE |du CE )",
    "CJA": "(?P<CJA>du Code de justice administrative|CJA|du CJA)",
}

CODE_REGEX = "|".join(CODE_DICT.values())
ARTICLE_P = f"{ARTICLE_REGEX}(?P<ref>.*?)({CODE_REGEX}$)"

JURI_PATTERN = re.compile(ARTICLE_P, flags=re.I)
ACCEPTED_EXTENSIONS = ("odt", "pdf", "docx", "doc")

def parse_doc(file_path):
    doc_name, doc_ext = file_path.split("/")[-1].split(".")
    print(".".join([doc_name, doc_ext]))
    if doc_ext not in ACCEPTED_EXTENSIONS:
        raise Exception("Extension incorrecte: les fichiers acceptés terminent par *.odt, *docx, *.pdf")
        
    full_text = []
    if doc_ext == "docx":
        with open(file_path, "r") as f:
            document = docx.Document(f.read())
            paragraphs = document.paragraphs
            for i in range(len(paragraphs)):
                full_text.append((paragraphs[i].text))
        
    elif doc_ext == "pdf":
        with open(file_path, "rb") as f:    
            reader = PdfReader(f)
            paragraphs = reader.pages
            for i in range(len(paragraphs)):
                page = reader.pages[i]
                full_text.append((page.extract_text()))
        
    elif doc_ext == "odt":
        with open(file_path, "r") as f:
            document = load(f)
            paragraphs = document.getElementsByType(text.P)
            for i in range(len(paragraphs)):
                full_text.append((teletype.extractText(paragraphs[i])))
    
    print(len(paragraphs), "paragraphs/pages")
    # print(full_text)
    full_text = re.sub("\r|\n|\t", " ", "".join(full_text))
    # paragraphs = [p for p in full_text.split("\n") if re.search(ARTICLE_REGEX, p) is not None and p.strip() != ""]
    
    # print(len(paragraphs))
    # print(paragraphs)
    print (full_text)
    for i, match in enumerate(re.finditer(JURI_PATTERN, full_text)):
        needle = match.groupdict()
        qualified_needle = {key: value for key, value in needle.items() if value is not None}
        print(i+1, qualified_needle)
        
    
if __name__== "__main__":
    test_path = "./tests/docs/"
    for f in os.listdir(test_path): 
        file_abspath = os.path.join(test_path, f)
        if os.path.isfile(file_abspath):
            print(file_abspath)
            # try:
            parse_doc(file_abspath)
            # except FileNotFoundError:
            #     print(f"{file_abspath} not found")
            #     pass
            # except Exception as e:
            #     print(e)
            #     pass