import requests
import os
import time
from dotenv import load_dotenv
import pytest
from test_002_code_references import get_code_full_name_from_short_code

API_ROOT_URL = "https://sandbox-api.piste.gouv.fr/dila/legifrance-beta/lf-engine-app/"
# API_ROOT_URL =  "https://api.piste.gouv.fr/dila/legifrance-beta/lf-engine-app/",



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


def get_article_uid(short_code_name, article_number, headers):
    """
    GET the article uid given by [Legifrance API](https://developer.aife.economie.gouv.fr/index.php?option=com_apiportal&view=apitester&usage=api&apitab=tests&apiName=L%C3%A9gifrance+Beta&apiId=426cf3c0-1c6d-46ba-a8b0-f79289086ed5&managerId=2&type=rest&apiVersion=1.6.2.5&Itemid=402&swaggerVersion=2.0&lang=fr)

    Arguments:
        code_name: Nom du code de droit français (version longue)
        article_number: Référence de l'article mentionné (version normalisée eg. L25-67)

    Returns:
        article_uid: Identifiant unique de l'article dans Legifrance or None

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



class TestOAuthLegiFranceAPI:
    def test_token_requests(self):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        json_response = get_legifrance_auth(client_id, client_secret)
        assert "Authorization" in json_response
        assert json_response["Authorization"].startswith("Bearer")

    def test_token_requests_wrong_credentials(self):
        load_dotenv()
        client_id = os.getenv("API_KEY2")
        client_secret = os.getenv("API_SECRET2")
        with pytest.raises(ValueError) as exc_info:
            json_response = get_legifrance_auth(client_id, client_secret)
            assert (
                str(exc_info.value)
                == "No credential: client_id or/and client_secret are not set. \nPlease register your API at https://developer.aife.economie.gouv.fr/"
            ), str(exc_info.value)


class TestGetArticleId:
    def test_get_article_uid(self):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        headers = get_legifrance_auth(client_id, client_secret)
        article = get_article_uid("CCIV", "1120", headers)
        assert article == "LEGIARTI000032040861", article

    @pytest.mark.parametrize(
        "input_expected",
        [
            ("CCONSO", "L121-14", "LEGIARTI000032227262"),
            ("CCONSO", "R742-52", "LEGIARTI000032808914"),
            ("CSI", "L622-7", "LEGIARTI000043540586"),
            ("CSI", "R314-7", "LEGIARTI000037144520"),
        ],
    )
    def test_get_article_uid(self, input_expected):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        code_name, art_num, expected = input_expected
        headers = get_legifrance_auth(client_id, client_secret)
        article_uid = get_article_uid(code_name, art_num, headers)
        assert expected == article_uid

    def test_get_article_uid_wrong_article_num(self):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        headers = get_legifrance_auth(client_id, client_secret)
        article_uid = get_article_uid("CCIV", "11-20", headers)
        assert article_uid == None, article_uid

    def test_get_article_uid_wrong_code_name(self):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        headers = get_legifrance_auth(client_id, client_secret)

        with pytest.raises(ValueError) as exc_info:
            # Note: Le code est sensible à la casse.
            # FEATURE: faire une base de référence insensible à la casse
            article_uid = get_article_uid("Code Civil", "1120", headers)
            assert str(exc_info.value) == "", str(exc_info.value)
            assert article_uid == None, article_uid


class TestGetArticleContent:
    def test_get_article_full_content(
        self, input_id=("CCONSO", "L121-14", "LEGIARTI000032227262")
    ):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        headers = get_legifrance_auth(client_id, client_secret)
        article_num, code, article_uid = input_id
        article_content = get_article_content(article_uid, headers)
        assert (
            article_content["url"]
            == "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032227262"
        ), article_content["url"]
        assert article_content["dateDebut"] == 1467331200000, article_content[
            "dateDebut"
        ]
        assert article_content["dateFin"] == 32472144000000, article_content["dateFin"]
        # assert article_content["nb_versions"] == 1, article_content["nb_versions"]
        assert article_content["articleVersions"][0] == {
            "dateDebut": 1467331200000,
            "dateFin": 32472144000000,
            "etat": "VIGUEUR",
            "id": "LEGIARTI000032227262",
            "numero": None,
            "ordre": None,
            "version": "1.0",
        }, article_content["articleVersions"][0]

    @pytest.mark.parametrize(
        "input_id",
        [
            ("CCONSO", "L121-14", "LEGIARTI000032227262"),
            ("CCONSO", "R742-52", "LEGIARTI000032808914"),
            ("CSI", "L622-7", "LEGIARTI000043540586"),
            ("CSI", "R314-7", "LEGIARTI000037144520"),
        ],
    )
    def test_get_article_content(self, input_id):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        headers = get_legifrance_auth(client_id, client_secret)
        article_num, code, article_uid = input_id
        article_content = get_article_content(article_uid, headers)
        assert (
            article_content["url"]
            == f"https://www.legifrance.gouv.fr/codes/article_lc/{article_uid}"
        ), article_content["url"]
        assert type(article_content["dateDebut"]) == int
        assert type(article_content["dateFin"]) == int
        assert article_content["nb_versions"] >= 1, article_content["nb_versions"]
