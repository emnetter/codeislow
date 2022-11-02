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
    return full_text


class TestFileParsing:
    def test_wrong_extension(self):
        """testing accepted extensions"""
        file_paths = ["document.rtf", "document.md", "document.xlsx"]
        with pytest.raises(ValueError) as e:
            for file_path in file_paths:
                parse_doc(file_path)
                assert e == "Extension incorrecte: les fichiers acceptés terminent par *.odt, *.docx, *.doc,  *.pdf"

    def test_wrong_file_path(self):
        """testing FileNotFound Error"""
        filepath = "./document.doc"
        with pytest.raises(FileNotFoundError) as e:
            parse_doc(filepath)
            assert e == "", e

    def test_content(self):
        """test content text"""
        file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf", "testnew.odt"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            full_text = parse_doc(abspath)
            doc_name, doc_ext = abspath.split("/")[-1].split(".")
            assert doc_name == "newtest" or doc_name == "testnew"
            if abspath.endswith(".pdf"):
                assert len(full_text) == 23, (len(full_text), abspath)
            else:
                assert len(full_text) == 22, (len(full_text), abspath)
            assert any("art." in _x for _x in full_text) is True
            assert any("Art." in _x for _x in full_text) is True
            assert any("Code" in _x for _x in full_text) is True
