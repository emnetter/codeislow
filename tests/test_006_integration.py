#!/usr/bin/env python

import os
from dotenv import load_dotenv
from test_001_parsing import parse_doc
from test_003_matching import get_matching_result_item
from test_004_request import get_article

def main(file_path, selected_codes=None, pattern_format="article_code", past=3, future=3):
    load_dotenv()
    
    client_id = os.getenv("API_KEY")
    client_secret = os.getenv("API_SECRET")
    #parse
    full_text = parse_doc(file_path)
    # matching_results = yield from get_matching_result_item(full_text,selected_codes, pattern_format)
    for code, article_nb in get_matching_result_item(full_text,selected_codes, pattern_format):
        #request and check validity
        yield get_article(code, article_nb, client_id, client_secret, past_year_nb=past, future_year_nb=future)



class TestMainProcess:
    def test_main_default(self):
        #usert input set to defaults
        past=3
        future=3
        selected_codes = None
        pattern_format = "article_code"
        file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            for result in main(file_path):
                assert isinstance(result, dict), result