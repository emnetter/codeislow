#!/usr/bin/env python3
# coding: utf-8
import os
from dotenv import load_dotenv

import pytest

from test_request_003 import MAIN_CODELIST, get_legifrance_auth, get_article_uid,  get_article_content

def check_validity(years_before, years_after, dateDebut, dateFin):
    """
    Controler le status de l'article: pas de modifications, prochaine mise à jour prochaine, modifié le

    Arguments:
        year_before: int representant le nombre d'année avant
        year_après: int representant le nombre d'année après
        dateDebut: int représentant la date de création de l'article au standard epoch
        dateFin: int représentant la date d'expiration de l'article au standard epoch
    Return:
        status: "Pas de modification", "Modifié le", "Valable jusqu'au"
        status_code: 204, 301, 302
    Raise:
        Exception(ConversionError) Erreur de conversion de epoch en date
    """
    status = "Pas de modification"
    status_code = 204
    return {"status": status, "status_code": status_code}


def get_article(code_name, article_number, client_id, client_secret):
    """
    Accéder aux informations de status de l'article
    
    Arguments:
        code_name: Nom du code de loi française dans sa version longue
        article_number: NUméro de l'article de loi normalisé ex. R25-67 L214 ou 2667-1-1
    Returns:
        article: Un dictionnaire json avec le texte les dates de début et de fin, l'url, les versions de l'article   
    Raise: 
        Exception(Indisponible): L'article n'a pas été trouvé
        ValueError(Code indisponible): Le nom du code est incorrect/ n'a pas été trouvé
    """
    article = {
        "code_full_name": MAIN_CODELIST[code_name],
        "code_short_name": code_name,
        "number": article_number
    }
    article_id = get_article_uid(code_name, article_number, headers=get_legifrance_auth(client_id, client_secret))
    if article_id is None:
        article["status_code"] = 404
        article["status"] = "Indisponible"
        article["id"] = None
        return article
    article_content = get_article_content(article_id, headers=get_legifrance_auth(client_id, client_secret))
    article.update(article_content)
    return article

class TestGetArticle:
    def test_get_single_article(self):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        article = get_article("CCONSO","L121-14", client_id, client_secret)
        assert article["dateDebut"] == 1467331200000, article["dateDebut"]
        assert article["dateFin"] == 32472144000000, article["dateFin"]
        assert article["url"] == "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032227262", article["url"]
        assert article["texte"] == "Le paiement résultant d'une obligation législative ou réglementaire n'exige pas d'engagement exprès et préalable."
        assert article["code_full_name"] == "Code de la consommation", article["code_full_name"]
        assert article["code_short_name"] == "CCONSO", article["code_short_name"]
        assert article["nb_versions"] == 1, article["nb_versions"]

    @pytest.mark.parametrize("input_expected", [("CCONSO","L121-14", 'LEGIARTI000032227262'), ("CCONSO","R742-52","LEGIARTI000032808914"), ("CSI","L622-7","LEGIARTI000043540586"), ("CSI","R314-7","LEGIARTI000037144520"), 
    ("CGCT","L1424-71", "LEGIARTI000028529379"), ("CJA", "L121-2", "LEGIARTI000043632528"), ("CESEDA", "L753-1", "LEGIARTI000042774802"), ("CENV", "L124-1", "LEGIARTI000033140333")])
    def test_get_articles(self, input_expected):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        code_short_name, art_num, art_id = input_expected
        article = get_article(code_short_name,art_num, client_id, client_secret)
        assert article["id"] == art_id, (code_short_name, art_num, article["id"])
        assert article["code_short_name"] == code_short_name, article["code_short_name"]
        assert article["code_full_name"] == MAIN_CODELIST[code_short_name], article["code_full_name"]

