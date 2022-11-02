#!/usr/bin/env python

import os
from dotenv import load_dotenv
from test_001_parsing import parse_doc
from test_002_matching import match_code_and_articles, gen_matching_results
from test_004_check import get_article

def main_process_gen(file_path, past=3, future=3):
    full_text = parse_doc(file_path)
    load_dotenv()
    client_id = os.getenv("API_KEY")
    client_secret = os.getenv("API_SECRET")
    for code, code_name, article in gen_matching_results(full_text):
        yield get_article(code_name, article, client_id, client_secret, past_year_nb=past, future_year_nb=future)

def main_static_process(file_path, past=3, future=3):
    full_text = parse_doc(file_path)
    load_dotenv()
    client_id = os.getenv("API_KEY")
    client_secret = os.getenv("API_SECRET")
    matching_results = match_code_and_articles(full_text)
    full_results = []
    for code_name, matches in matching_results.items():
        for article in matches:
            full_article = get_article(code_name, article, client_id, client_secret, past_year_nb=past, future_year_nb=future)
            article_display = article["full_"]
            full_results.append(full_article)
    return full_results


class TestMainStaticProcess:
    # def test_main_process(self):
    #     past=3
    #     future=3
    #     file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf"]
    #     for file_path in file_paths:
    #         abspath = os.path.join(
    #             os.path.dirname(os.path.realpath(__file__)), file_path
    #         )
    #         results = main_static_process(abspath, past, future)
    #         assert len(results) == 37, len(results)
    #         assert results[0] == {}, results[0]
    #         # full_text = parse_doc(abspath)
    #         # matching_results = match_code_and_articles(full_text)
    def test_main_process_gen(self):
        past=3
        future=3
        file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            for result in main_process_gen(abspath, past, future):
                assert len(result) == 3, len(result)
                assert result[0] == "", result[0]


