#!/usr/bin/env python3
# filename: request_api.py
"""
Module pour requeter l'API

- authentification
- get_article_id
- get_article_content
- get_article: module complet avec le status de l'article
"""

import requests
import datetime
import time
from dotenv import load_dotenv
import pytest
from code_references import get_code_full_name_from_short_code
from check_validity import convert_epoch_to_datetime, convert_datetime_to_str, get_validity_status, time_delta

API_ROOT_URL = "https://sandbox-api.piste.gouv.fr/dila/legifrance-beta/lf-engine-app/"
# API_ROOT_URL =  "https://api.piste.gouv.fr/dila/legifrance-beta/lf-engine-app/",



def get_legifrance_auth(client_id, client_secret):
    """
    Get authorization token from LEGIFRANCE API

    Arguments
    ---------
    client_id: str
        OAUTH CLIENT key provided by API
    client_secret: str
        OAUTH SECRET key provided by API

    Returns
    ---------
    authorization_header: dict
        a header composed of a json dict with access_token

    Raise
    ------
    Exception: 
        No credentials have been set. Client_id or client_secret is None
    Exception: 
        Invalid credentials. Request to authentication server failed with 400 or 401 error
    """

    TOKEN_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
    # TOKEN_URL = "https://sandbox-oauth.aife.economie.gouv.fr/api/oauth/token"

    if client_id is None or client_secret is None:
        # return HTTPError(401, "No credential have been set")
        raise ValueError(
            "No credential: client_id or/and client_secret are not set. \nPlease register your API at https://developer.aife.economie.gouv.fr/"
        )
    session = requests.Session()
    with session as s:
        res = s.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "openid",
            },
        )

        if res.status_code in [400, 401]:
            # return HTTPError(res.status_code, "Unauthorized: invalid credentials")
            raise Exception(f"HTTP Error code: {res.status_code}: Invalid credentials")
        token = res.json()
    access_token = token["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def get_article_uid(short_code_name, article_number, headers):
    """
    GET the article uid given by [Legifrance API](https://developer.aife.economie.gouv.fr/index.php?option=com_apiportal&view=apitester&usage=api&apitab=tests&apiName=L%C3%A9gifrance+Beta&apiId=426cf3c0-1c6d-46ba-a8b0-f79289086ed5&managerId=2&type=rest&apiVersion=1.6.2.5&Itemid=402&swaggerVersion=2.0&lang=fr)

    Arguments
    ---------
    code_name:str 
        Nom du code de droit français (version courte)
    article_number: str 
        Référence de l'article mentionné (version normalisée eg. L25-67)

    Returns
    --------
    article_uid: str
        Identifiant unique de l'article dans Legifrance LEGIART000xxxx or None
    Raises
    ------
    ValueError:
        Le nom du code est incorrect
    Exception:
        La requete a échoué response.status_code [400-500] 
    """
    long_code = get_code_full_name_from_short_code(short_code_name)
    if long_code is None:
        raise ValueError(f"`{short_code_name}` not found in the supported Code List")

    session = requests.Session()

    today_epoch = int(time.time()) * 1000
    data = {
        "recherche": {
            "champs": [
                {
                    "typeChamp": "NUM_ARTICLE",
                    "criteres": [
                        {
                            "typeRecherche": "EXACTE",
                            "valeur": article_number,
                            "operateur": "ET",
                        }
                    ],
                    "operateur": "ET",
                }
            ],
            "filtres": [
                {"facette": "NOM_CODE", "valeurs": [long_code]},
                {"facette": "DATE_VERSION", "singleDate": today_epoch},
            ],
            "pageNumber": 1,
            "pageSize": 10,
            "operateur": "ET",
            "sort": "PERTINENCE",
            "typePagination": "ARTICLE",
        },
        "fond": "CODE_DATE",
    }
    with session as s:
        response = s.post(
            "/".join([API_ROOT_URL, "search"]), headers=headers, json=data
        )
        if response.status_code > 399:
            # print(response)
            # return None
            raise Exception(f"Error {response.status_code}: {response.reason}")

        article_informations = response.json()
    if not article_informations["results"]:
        return None

    results = article_informations["results"]
    if len(results) == 0:
        return None
    else:
        # get the first result
        try:
            return results[0]["sections"][0]["extracts"][0]["id"]
        except IndexError:
            return None
    


def get_article_content(article_id, headers):
    """
    GET article_content from LEGIFRANCE API using POST /consult/getArticle https://developer.aife.economie.gouv.fr/index.php?option=com_apiportal&view=apitester&usage=api&apitab=tests&apiName=L%C3%A9gifrance+Beta&apiId=426cf3c0-1c6d-46ba-a8b0-f79289086ed5&managerId=2&type=rest&apiVersion=1.6.2.5&Itemid=402&swaggerVersion=2.0&lang=fr

    Arguments
    ----------
    article_id: str
        article uid eg. LEGIARTI000006307920
    Returns
    -------
    article_content: dict
        a dictionnary with the full content of article
    Raise
    -------
    Exception 
        response.status_code [400-500]
    """
    data = {"id": article_id}
    session = requests.Session()
    with session as s:

        response = s.post(
            "/".join([API_ROOT_URL, "consult", "getArticle"]),
            headers=headers,
            json=data,
        )

        if response.status_code > 399:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        article_content = response.json()
    try:
        raw_article = article_content["article"]
        # FEATURE récupérer tous les titres et sections d'un article
        article = {
            "url": f"https://www.legifrance.gouv.fr/codes/article_lc/{article_id}"
        }
        for k in [
            "id",
            "num",
            "texte",
            "etat",
            "dateDebut",
            "dateFin",
            "articleVersions",
        ]:
            article[k] = raw_article[k]
        # FEATURE - integrer les différentes versions
        article["nb_versions"] = len(article["articleVersions"])
        
        return article
    except KeyError:
        return None


def get_article_content_by_id_and_article_nb(article_id, article_num, headers):
    """
    Récupère un Article en fonction de son ID et Numéro article depuis API Legifrance GET /consult getArticleWithIdAndNum
    Arguments
    ---------
    article_id: str
        article uid eg. LEGIARTI000006307920
    article_num: str
        numéro de l'article standardisé eg. "3-45", "L214", "R25-64"
    Returns
    -------
    article_content: dict
        a dictionnary with the full content of article
    Raise
    -----
    Exception
        response.status_code [400-500]
    """

    data = {"id": article_id, "num": article_num}

    session = requests.Session()
    with session as s:

        response = s.post(
            "/".join([API_ROOT_URL, "consult", "getArticleWithIdandNum"]),
            headers=headers,
            json=data,
        )
        if response.status_code > 399:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        article_content = response.json()
    return article_content["article"]

def get_article(short_code_name, article_number, client_id, client_secret, past_year_nb=3, future_year_nb=3):
    """
    Accéder aux informations simplifiée de l'article

    Arguments
    ---------
    long_code_name: str
        Nom du code de loi française dans sa version longue
    article_number: str
        Numéro de l'article de loi normalisé ex. R25-67 L214 ou 2667-1-1
    Returns
    --------
    article: str
        Un dictionnaire json avec code (version courte), article (numéro), status, status_code, color, url, text, id, start_date, end_date, date_debut, date_fin 
    """
    
    article = {
        "code": short_code_name,
        "code_full_name": get_code_full_name_from_short_code(short_code_name),
        "article": article_number,
        "status_code": 200,
        "status": "OK",
        "color": "grey",
        "url": "",
        "texte": "",
        "id": get_article_uid(
            short_code_name, article_number, headers=get_legifrance_auth(client_id, client_secret)
        )
    }
    if article["id"] is None:
        article["color"] = "red"
        article["status_code"] = 404
        article["status"] = "Indisponible"
        return article
    article_content = get_article_content(
        article["id"], headers=get_legifrance_auth(client_id, client_secret)
    )
    article["texte"] = article_content["texte"]
    article["url"] = article_content["url"]
    article["start_date"] = convert_epoch_to_datetime(article_content["dateDebut"])
    article["end_date"] = convert_epoch_to_datetime(article_content["dateFin"])
    article["status_code"], article["status"], article["color"] = get_validity_status(article["start_date"], article["end_date"], past_year_nb, future_year_nb)
    article["date_debut"] = convert_datetime_to_str(article["start_date"]).split(" ")[0]
    article["date_fin"] = convert_datetime_to_str(article["end_date"]).split(" ")[0]
    return article


