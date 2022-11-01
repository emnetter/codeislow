#!/usr/bin/env python

import pytest
import os

import docx
from PyPDF2 import PdfReader
from odf import text, teletype
from odf.opendocument import load

ACCEPTED_EXTENSIONS = ("odt", "pdf", "docx", "doc")


def parse_doc(file_path):
    """
    Parsing document
    Arguments:
        file_path: a string representing the absolute filepath of the document
    Returns:
        full_text: a list of sentences
    Raises:
        Exception: Extension incorrecte. Les types de fichiers supportés sont odt, doc, docx, pdf
        FileNotFoundError: File has not been found. File_path must be incorrect
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
            paragraphs = len(document.getElementsByType(text.P))
            for i in range(paragraphs):
                full_text.append((teletype.extractText(paragraphs[i])))
    else:
        # if doc_ext in ["docx", "doc"]:
        with open(file_path, "rb") as f:
            document = docx.Document(f)
            paragraphs = document.paragraphs
            for i in range(len(paragraphs)):
                full_text.append((paragraphs[i].text))
    full_text = [n for n in full_text if n not in ["\n", "", " "]]
    return full_text