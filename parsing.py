#!/usr/bin/env python
# filename: parsing.py

"""
Parsing file module:

Load document with the accepted extensions and transform into list of text

"""


import docx
from PyPDF2 import PdfReader
from odf import text, teletype
from odf.opendocument import load

ACCEPTED_EXTENSIONS = ("odt", "pdf", "docx", "doc")


def parse_doc(file_path):
    """
    Parcourir le document pour en extraire le texte 
    Arguments
    ----------
    file_path: str 
        absolute filepath of the document
    Returns
    ----------
    full_text: array 
        a list of sentences.
    Raises
    ----------
    Exception: 
        Extension incorrecte. Les types de fichiers supportés sont odt, doc, docx, pdf
    FileNotFoundError: 
        File has not been found. File_path must be incorrect
    """
    
    doc_name, doc_ext = file_path.split("/")[-1].split(".")
    if doc_ext not in ACCEPTED_EXTENSIONS:
        raise ValueError(
            "Extension incorrecte: les fichiers acceptés terminent par *.odt, *.docx, *.doc,  *.pdf"
        )

    full_text = []
    if doc_ext == "pdf":
        with open(file_path, "rb") as f:
            reader = PdfReader(f)

            for i in range(len(reader.pages)):
                page = reader.pages[i]
                full_text.extend((page.extract_text()).split("\n"))

    elif doc_ext == "odt":
        with open(file_path, "rb") as f:
            document = load(f)
            paragraphs = document.getElementsByType(text.P)
            for i in range(len(paragraphs)):
                full_text.append((teletype.extractText(paragraphs[i])))
    else:
        # if doc_ext in ["docx", "doc"]:
        with open(file_path, "rb") as f:
            document = docx.Document(f)
            paragraphs = document.paragraphs
            for i in range(len(paragraphs)):
                full_text.append((paragraphs[i].text))
    full_text = [n for n in full_text if n not in ["\n", "", " "]]
    os.remove(file_path)
    return full_text