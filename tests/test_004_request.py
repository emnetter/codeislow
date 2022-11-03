import requests
import os
import datetime
import time
from dotenv import load_dotenv
import pytest
from test_002_code_references import get_code_full_name_from_short_code
from test_005_check_validity import convert_epoch_to_datetime, convert_datetime_to_str, get_validity_status, time_delta

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

def get_article(short_code_name, article_number, client_id, client_secret, past_year_nb=3, future_year_nb=3):
    """
    Accéder aux informations simplifiée de l'article

    Arguments:
        long_code_name: Nom du code de loi française dans sa version longue
        article_number: NUméro de l'article de loi normalisé ex. R25-67 L214 ou 2667-1-1
    Returns:
        article: Un dictionnaire json avec code (version courte), article (numéro), status, status_code, color, url, text, id, start_date, end_date, date_debut, date_fin 
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


class TestGetArticle:
    def test_get_single_article(self):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        article = get_article("CCONSO", "L121-14", client_id, client_secret, past_year_nb=3, future_year_nb=3)
        assert article["start_date"] == datetime.datetime(2016, 7, 1, 0, 0), article[
            "start_date"
        ]
        assert article["end_date"] == datetime.datetime(2999, 1, 1, 0, 0), article[
            "end_date"
        ]
        assert (
            article["url"]
            == "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032227262"
        ), article["url"]
        assert (
            article["texte"]
            == "Le paiement résultant d'une obligation législative ou réglementaire n'exige pas d'engagement exprès et préalable."
        )
        assert article["code"] == "CCONSO", article[
            "code"
        ]
        assert article["article"] == "L121-14"
        assert article["status"] == "Pas de modification"
        assert article["status_code"] == 204
        assert article["id"] == "LEGIARTI000032227262"
        assert article["color"] == "green"
        # assert article["nb_versions"] == 1, article["nb_versions"]

    @pytest.mark.parametrize(
        "input_expected",
        [
            ("CCONSO", "L121-14", "LEGIARTI000032227262",204),
            ("CCONSO", "R742-52", "LEGIARTI000032808914",204),
            ("CSI", "L622-7", "LEGIARTI000043540586", 301),
            ("CSI", "R314-7", "LEGIARTI000037144520",204),
            ("CGCT", "L1424-71", "LEGIARTI000028529379", 204),
            ("CJA", "L121-2", "LEGIARTI000043632528",301),
            ("CESEDA", "L753-1", "LEGIARTI000042774802", 301),
            ("CENV", "L124-1", "LEGIARTI000033140333", 204),
        ],
    )
    def test_get_multiple_articles(self, input_expected):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        code_short_name, art_num, art_id, status_code = input_expected
        article = get_article(code_short_name, art_num, client_id, client_secret)
        assert article["id"] == art_id, (code_short_name, art_num, article["id"])
        # assert article["short_code"] == code_short_name, article["code_short_name"]
        # assert article["long_code"] == CODE_REFERENCE[code_short_name], article[
        #     "long_code"
        # ]
        assert article["status_code"] == status_code, (status_code, code_short_name,art_num)

    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "CCONSO",
                "L121-14",
                datetime.datetime(2016, 7, 1, 0, 0),
                datetime.datetime(2999, 1, 1, 0, 0),
            ),
            (
                "CCONSO",
                "R742-52",
                datetime.datetime(2016, 7, 1, 0, 0),
                datetime.datetime(2999, 1, 1, 0, 0),
            ),
            (
                "CSI",
                "L622-7",
                datetime.datetime(2021, 5, 27, 0, 0),
                datetime.datetime(2022, 11, 26, 0, 0),
            ),
            (
                "CSI",
                "R314-7",
                datetime.datetime(2018, 8, 1, 0, 0),
                datetime.datetime(2999, 1, 1, 0, 0),
            ),
            (
                "CGCT",
                "L1424-71",
                datetime.datetime(2015, 1, 1, 0, 0),
                datetime.datetime(2999, 1, 1, 0, 0),
            ),
            (
                "CJA",
                "L121-2",
                datetime.datetime(2022, 1, 1, 0, 0),
                datetime.datetime(2999, 1, 1, 0, 0),
            ),
            (
                "CESEDA",
                "L753-1",
                datetime.datetime(2021, 5, 1, 0, 0),
                datetime.datetime(2999, 1, 1, 0, 0),
            ),
            (
                "CENV",
                "L124-1",
                datetime.datetime(2016, 1, 1, 0, 0),
                datetime.datetime(2999, 1, 1, 0, 0),
            ),
        ],
    )
    def test_get_multiple_articles_validity(self, input_expected):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        code_short_name, art_num, start_date, end_date = input_expected
        article = get_article(code_short_name, art_num, client_id, client_secret)
        assert article["start_date"] == start_date, (
            article["start_date"],
            code_short_name,
            art_num,
        )
        assert article["end_date"] == end_date, (
            article["end_date"],
            code_short_name,
            art_num,
        )
    
    @pytest.mark.parametrize(
        "input_expected",
        [
            ("CCONSO", "R11-14", None),
            ("CCONSO", "742-52", None),
            ("CSI", "622-7", None),
            ("CSI", "314-7", None),
            ("CGCT", "1424-71", None),
            ("CJA", "121-2", None),
            ("CESEDA", "753-1", None),
            ("CENV", "124-1", None),
        ],
    )
    def test_get_not_found_articles(self, input_expected):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        code_short_name, art_num, art_id = input_expected
        article = get_article(code_short_name, art_num, client_id, client_secret)
        assert article["id"] == art_id, (code_short_name, art_num, article["id"])
        # assert article["code_short_name"] == code_short_name, article["code_short_name"]
        # assert article["code_full_name"] == CODE_REFERENCE[code_short_name], article[
        #     "code_full_name"
        # ]
        assert article["status_code"] == 404


class TestTimeDelta:
    def test_time_delta_3(self):
        past_3, future_3 = time_delta("-", 3), time_delta("+", 3)
        today = datetime.date.today()
        assert past_3.year == today.year - 3, (past_3.year, past_3.month, past_3.day)
        assert future_3.year == today.year + 3, (
            future_3.year,
            future_3.month,
            future_3.day,
        )

    def test_time_delta_2(self):
        today = datetime.date.today()
        past_2, future_2 = time_delta("-", 2), time_delta("+", 2)
        assert past_2.year == (today.year) - 2, (past_2.year, past_2.month, past_2.day)
        assert future_2.year == (today.year) + 2, (
            future_2.year,
            future_2.month,
            future_2.day,
        )

    def test_time_delta_wrong_op(self):

        with pytest.raises(ValueError) as e:
            past_mul3 = time_delta("*", 3)
            assert e == "ValueError: Wrong operator", e

    def test_time_delta_wrong_nb(self):
        with pytest.raises(TypeError) as e:
            past_mul3 = time_delta("+", "9")
            assert e == "TypeError: Year must be an integer", e


class TestValidityArticle:
    def test_validity_soon_deprecated(self):
        """ """
        year_nb = 2
        start = datetime.datetime(2018, 1, 1, 0, 0, 0)
        past_boundary = time_delta("-", year_nb)
        end = datetime.datetime(2023, 1, 1, 0, 0, 0)
        future_boundary = time_delta("+", year_nb)
        # QUESTION: avons nous besoin de différencier avant et après?
        status_code, status_msg, color = get_validity_status(start, end, year_nb, year_nb)
        assert end < future_boundary, (
            bool(end < future_boundary),
            end,
            future_boundary,
        )
        assert status_code == 302, status_code
        assert status_msg == "Valable jusqu'au 01/01/2023", status_msg
        assert color=="orange", color
    def test_validity_recently_modified(self):
        year_nb = 2
        start = datetime.datetime(2022, 8, 4, 0, 0, 0)
        past_boundary = time_delta("-", year_nb)
        end = datetime.datetime(2025, 1, 1, 0, 0, 0)
        future_boundary = time_delta("+", year_nb)
        # QUESTION: avons nous besoin de différencier avant et après?
        assert start > past_boundary, (start > past_boundary, start, past_boundary)
        status_code, status_msg, color = get_validity_status(start, end, year_nb, year_nb)
        assert status_code == 301, status_code
        assert status_msg == "Modifié le 04/08/2022", status_msg
        assert color=="yellow", color
    def test_validity_ras(self):
        year_nb = 2
        start = datetime.datetime(1801, 8, 4, 0, 0, 0)
        past_boundary = time_delta("-", year_nb)
        end = datetime.datetime(2040, 1, 1, 0, 0, 0)
        future_boundary = time_delta("+", year_nb)
        # QUESTION: avons nous besoin de différencier avant et après?
        assert start < past_boundary, (start < past_boundary, start, past_boundary)
        assert end > future_boundary, (end > future_boundary, end, future_boundary)
        status_code, status_msg, color = get_validity_status(start, end, year_nb, year_nb)
        assert status_code == 204, status_code
        assert status_msg == "Pas de modification", status_msg
        assert color=="green", color