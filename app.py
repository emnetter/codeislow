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
        # article = get_article(code, article_nb, client_id, client_secret, past_year_nb=past, future_year_nb=future)
        # print(article)
        yield get_article(code, article_nb, client_id, client_secret, past_year_nb=past, future_year_nb=future)



