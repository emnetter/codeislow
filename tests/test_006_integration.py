#!/usr/bin/env python

import os
import datetime
from dotenv import load_dotenv
from test_001_parsing import parse_doc
from test_003_matching import match_code_and_articles, gen_matching_results
from test_005_check import get_article

def main_process_gen(file_path, selected_codes, past=3, future=3):
    load_dotenv()
    full_text = parse_doc(file_path)
    client_id = os.getenv("API_KEY")
    client_secret = os.getenv("API_SECRET")
    for code, article in gen_matching_results(full_text, selected_shortcodes):
        yield get_article(code, article, client_id, client_secret, past_year_nb=past, future_year_nb=future)

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
    return full_results


class TestMainProcess:
    # def test_main_static_process(self):
    #     past=3
    #     future=3
    #     file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf"]
    #     for file_path in file_paths:
    #         abspath = os.path.join(
    #             os.path.dirname(os.path.realpath(__file__)), file_path
    #         )
    #         results = main_static_process(abspath, past, future)
    #         assert len(results) == 37, len(results)
    #         assert results[0] == {
    #                 'article': '1120',
    #                 'code': 'CCIV',
    #                 'code_full_name': 'Code civil',
    #                 'color': 'green',
    #                 'date_debut': '01/10/2016',
    #                 'date_fin': '01/01/2999',
    #                 'end_date': datetime.datetime(2999, 1, 1, 0, 0),
    #                 'id': 'LEGIARTI000032040861',
    #                 'start_date': datetime.datetime(2016, 10, 1, 0, 0),
    #                 'status': 'Pas de modification',
    #                 'status_code': 204,
    #                 'texte': "Le silence ne vaut pas acceptation, à moins qu'il n'en résulte "
    #                         "autrement de la loi, des usages, des relations d'affaires ou de "
    #                         'circonstances particulières.',
    #                 'url': 'https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032040861'
    #                                       }, results[0]
    def test_main_process_gen(self):
        past=3
        future=3
        file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            for result in main_process_gen(abspath, past, future):
                assert len(result) == 13, len(result)
                # assert result[0] == 


