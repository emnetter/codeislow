import requests
import os
import time
from dotenv import load_dotenv
import pytest

API_ROOT_URL = "https://sandbox-api.piste.gouv.fr/dila/legifrance-beta/lf-engine-app/"
# API_ROOT_URL =  "https://api.piste.gouv.fr/dila/legifrance-beta/lf-engine-app/",

MAIN_CODELIST = {
    "CCIV": "Code civil",
    "CPRCIV": "Code de procédure civile",
    "CCOM": "Code de commerce",
    "CTRAV": "Code du travail",
    "CPI": "Code de la propriété intellectuelle",
    "CPEN": "Code pénal",
    "CPP": "Code de procédure pénale",
    "CASSUR": "Code des assurances",
    "CCONSO": "Code de la consommation",
    "CSI": "Code de la sécurité intérieure",
    "CSP": "Code de la santé publique",
    "CSS": "Code de la sécurité sociale",
    "CESEDA": "Code de l'entrée et du séjour des étrangers et du droit d'asile",
    "CGCT": "Code général des collectivités territoriales",
    "CPCE": "Code des postes et des communications électroniques",
    "CENV": "Code de l'environnement",
    "CJA": "Code de justice administrative",
}


def get_code_full_name_from_short_code(short_code):
    """
    Shortcut to get corresponding full_name from short_code

    Arguments:
        short_code: short form of Code eg. CCIV
    Returns:
        full_name: long form of code eg. Code Civil
    """
    try:
        return MAIN_CODELIST[short_code]
    except ValueError:
        return None


def get_short_code_from_full_name(full_name):
    """
    Shortcut to get corresponding short_code from full_name

    Arguments:
        full_name: long form of code eg. Code Civil
    Returns:
        short_code: short form of Code eg. CCIV
    """
    keys = [k for k, v in MAIN_CODELIST.items() if v == full_name]
    if len(keys) > 0:
        return keys[0]
    else:
        return None


def get_legifrance_auth(client_id, client_secret):
    """
    Get authorization token from LEGIFRANCE API

    Arguments:
        client_id: OAUTH CLIENT key provided by API
        client_secret: OAUTH SECRET key provided by API

    Returns:
        authorization_header: a header composed of a json dict with access_token

    Raise:
        Exception: No credentials have been set. Client_id or client_secret is None
        Exception: Invalid credentials. Request to authentication server failed with 400 or 401 error
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


def get_article_uid(code_name, article_number, headers):
    """
    GET the article uid given by [Legifrance API](https://developer.aife.economie.gouv.fr/index.php?option=com_apiportal&view=apitester&usage=api&apitab=tests&apiName=L%C3%A9gifrance+Beta&apiId=426cf3c0-1c6d-46ba-a8b0-f79289086ed5&managerId=2&type=rest&apiVersion=1.6.2.5&Itemid=402&swaggerVersion=2.0&lang=fr)

    Arguments:
        code_name: Nom du code de droit français (version longue)
        article_number: Référence de l'article mentionné (version normalisée eg. L25-67)

    Returns:
        article: un dictionnaire qui contient l'identifiant unique de l'article dans legifrance, le nom du code en version courte et en version longue
        article_uid: Identifiant unique de l'article dans Legifrance or None

    """
    if code_name in list(MAIN_CODELIST.keys()):
        code_short = code_name
        code_long = MAIN_CODELIST[code_name]
    elif code_name in list(MAIN_CODELIST.values()):
        code_long = code_name
        code_short = get_short_code_from_full_name(code_long)
    else:
        raise ValueError(f"`{code_name}` not found in the supported Code List")

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
                {"facette": "NOM_CODE", "valeurs": [code_long]},
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
        # get the first results
        try:
            article_uid = results[0]["sections"][0]["extracts"][0]["id"]
        except IndexError:
            return None
    # article = {
    #     "id": article_uid,
    #     "code_name_short": code_short,
    #     "code_name_long": code_long,
    # }
    return article_uid


def get_article_content(article_id, headers):
    """
    GET article_content from LEGIFRANCE API using POST /consult/getArticle https://developer.aife.economie.gouv.fr/index.php?option=com_apiportal&view=apitester&usage=api&apitab=tests&apiName=L%C3%A9gifrance+Beta&apiId=426cf3c0-1c6d-46ba-a8b0-f79289086ed5&managerId=2&type=rest&apiVersion=1.6.2.5&Itemid=402&swaggerVersion=2.0&lang=fr

    Arguments:
        article_id: article uid eg. LEGIARTI000006307920
    Returns:
        article_content: a dictionnary with the full content of article
    Raise:
         Exception : response.status_code [400-500]
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
    Arguments:
        article_id: article uid eg. LEGIARTI000006307920
        article_num: numéro de l'article standardisé eg. "3-45", "L214", "R25-64"
    Returns:
        article_content: a dictionnary with the full content of article
    Raise:
         Exception : response.status_code [400-500]
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


