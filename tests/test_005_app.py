#!/usr/bin/env python

import os
from dotenv import load_dotenv
from parsing import parse_doc
from matching import match_code_and_articles, gen_matching_results
from checking import get_article

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
            full_results.append(full_article)
            