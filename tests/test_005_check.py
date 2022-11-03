#!/usr/bin/env python3
# coding: utf-8
from datetime import datetime
import os
from re import T
from dotenv import load_dotenv
import datetime
from dateutil.relativedelta import relativedelta
import pytest

from test_004_request import (
    get_legifrance_auth,
    get_article_uid,
    get_article_content
)

from test_002_code_references import get_code_full_name_from_short_code


### TIME CONVERSION UTILS

def convert_date_to_datetime(date):
    return datetime.datetime.fromordinal(date.toordinal())


def convert_datetime_to_date(date_time):
    date_time.replace(hour=0, minute=0, second=0)
    return date_time


def convert_epoch_to_datetime(epoch):
    """convert epoch (seconds till 01/01/1970) to date"""
    return datetime.datetime.utcfromtimestamp(epoch / 1000)


def convert_datetime_to_epoch(date_time):
    """convert datetime to epoch"""
    epoch = datetime.datetime.utcfromtimestamp(0)
    # return date_time - epoch
    return (date_time - epoch).total_seconds() * 1000


def convert_date_to_str(date_time):
    """convert datetime into string format"""
    return datetime.datetime.strftime(date_time[:4], "%d/%m/%Y")


def convert_datetime_to_str(date_time):
    """convert datetime into string format"""
    return datetime.datetime.strftime(date_time, "%d/%m/%Y %H:%M:%S")


def convert_str_to_datetime(date_time):
    '''
    convert string format into datetime
    Arguments:
        date_str: string representation of a date
    Returns:
        date_time: datetime
    '''
    return datetime.datetime.strptime(date_time, "%d/%m/%Y %H:%M:%S")


def time_delta(operator, year_nb):
    """
    Calculer le différentiel de date selon l'opérator et le nombre d'années
    Arguments: 
        operator: chaine de caractère qui représente l'opérateur: - ou +
        year_nb: entier qui représente le nombre d'années
    Return:
        datetime_delta: objet datetime représentant la nouvelle date 
    """
    if operator not in ["-", "+"]:
        raise ValueError("Wrong operator")
    if not isinstance(year_nb, int):
        raise TypeError("Year must be an integer")
    today = datetime.date.today()
    if operator == "-":
        return convert_date_to_datetime(today.replace(year=today.year - year_nb))
    else:
        return convert_date_to_datetime(today.replace(year=today.year + year_nb))


def time_delta_to_epoch(operator, year_nb):
    """
    Calculer le différentiel de date selon l'opérator et le nombre d'années
    Arguments: 
        operator: chaine de caractère qui représente l'opérateur: - ou +
        year_nb: entier qui représente le nombre d'années
    Return:
        date_delta: timestamp représentant la nouvelle date 
    """
    
    return convert_datetime_to_epoch(time_delta(operator, year_nb))

def get_validity_status(start, end, year_before, year_after):
    """
    Verifier la validité de l'article à partir d'une plage de temps
    Arguments:
        year_before: Un entier qui correspond à un nombre d'année
        start: Un objet datetime représentant la date de création de l'article
        year_after: entier représentant un nombre d'année
        end: Un objet datetime représentant la date de fin de validité de l'article

    Returns:
        status_code: Un code de status qui s'inspire d'HTTP
        response: Un message de status
    """
    past_boundary = time_delta("-", year_before)
    future_boundary = time_delta("+", year_after)
    if start > past_boundary:
        return (301, "Modifié le {}".format(convert_datetime_to_str(start).split(" ")[0]), "yellow")
    if end < future_boundary:
        return (302, "Valable jusqu'au {}".format(convert_datetime_to_str(end).split(" ")[0]), "orange")
    if start < past_boundary and end > future_boundary:
        return (204, "Pas de modification", "green")

### FULL INTEGRATION 
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