#!/usr/bin/env python

import os
from dotenv import load_dotenv
from parsing import parse_doc
from matching import get_matching_result_item
from request_api import get_article

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

def load_result(file_path, selected_codes=None, pattern_format="article_code", past=3, future=3):
    '''
    Load result in HTML
    
    Arguments
    ---------
    filepath: str
        le chemin du fichier
    selected_codes: array
        la liste des codes (version abbréviée) à détecter
    pattern_format: str
        le format des références: Article xxx du Code yyy ou Code yyyy Article xxx
    past: int
        nombre d'années dans le passé
    future: int
        nombre d'années dans le futur
    Yields
    ------
    html_results: str
        resultat sous forme de cellule d'une table HTML
    '''
    load_dotenv()
    client_id = os.getenv("API_KEY")
    client_secret = os.getenv("API_SECRET")
    #parse
    full_text = parse_doc(file_path)
    # matching_results = yield from get_matching_result_item(full_text,selected_codes, pattern_format)
    for code, article_nb in get_matching_result_item(full_text,selected_codes, pattern_format):
        #request and check validity
        article = get_article(code, article_nb, client_id, client_secret, past_year_nb=past, future_year_nb=future)
        row = f"""
        <tr>
            <th scope="row"><a href='{article["url"]}'>{article["code"]} - {article["article"]}</a></th>
            <td><span class="badge badge-pill badge-{article["color"]}">{article["status"]}</span></td>
            <td>{article["texte"]}</td>
            <td>{article["date_debut"]}-{article["date_fin"]}</td>
        <tr>
        """
        yield(row)
        
        

