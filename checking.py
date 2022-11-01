#!/usr/bin/env python3
# coding: utf-8
from datetime import datetime
import os
from re import T
from dotenv import load_dotenv
import datetime
from dateutil.relativedelta import relativedelta
import pytest

from requesting import (
    MAIN_CODELIST,
    get_legifrance_auth,
    get_article_uid,
    get_article_content,
)


def convert_date_to_datetime(date):
    return datetime.datetime.fromordinal(date.toordinal())


# def convert_datetime_to_date(date_time):
#     date_time.replace(hour=0, minute=0, second=0)
#     return date_time


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


# def convert_str_to_datetime(date_time):
#     '''
#     convert string format into datetime
#     Arguments:
#         date_str: string representation of a date
#     Returns:
#         date_time: datetime
#     '''
#     return datetime.datetime.strptime(date_time, "%d/%m/%Y %H:%M:%S")


def time_delta(operator, year_nb):
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
    return convert_datetime_to_epoch(time_delta(operator, year_nb))

def get_validity_status(start, end, year_before, year_after):
    """
    Verifier la validité de l'article à partir d'une plage de temps
    Arguments:
        year_before: entier qui correspond à un nombre d'année
        start: Un object datetime représentant la date de création de l'article
        year_after: entier représentant un nombre d'année
        end: Un object datetime représentant la date de fin de validité de l'article

    Returns:
        status_code: Un code de status qui s'inspire d'HTTP
        response: Un message de status
    """
    past_boundary = time_delta("-", year_before)
    future_boundary = time_delta("+", year_after)
    if start > past_boundary:
        return (301, "Modifié le {}".format(convert_datetime_to_str(start)))
    if end < future_boundary:
        return (302, "Valable jusqu'au {}".format(convert_datetime_to_str(end)))
    if start < past_boundary and end > future_boundary:
        return (204, "Pas de modification")


def get_article(code_name, article_number, client_id, client_secret, past_year_nb=3, future_year_nb=3):
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
        "number": article_number,
        "status_code": 200,
        "status": "OK",
    }
    article_id = get_article_uid(
        code_name, article_number, headers=get_legifrance_auth(client_id, client_secret)
    )
    if article_id is None:
        article["status_code"] = 404
        article["status"] = "Indisponible"
        article["id"] = None
        return article
    article_content = get_article_content(
        article_id, headers=get_legifrance_auth(client_id, client_secret)
    )
    article.update(article_content)
    # convert epoch to datetime
    article["start_date"] = convert_epoch_to_datetime(article["dateDebut"])
    article["end_date"] = convert_epoch_to_datetime(article["dateFin"])
    article["status_code"], article["status"] = get_validity_status(article["start_date"], article["end_date"], past_year_nb, future_year_nb)
    article["date_debut"] = convert_datetime_to_str(article["start_date"])
    article["date_fin"] = convert_datetime_to_str(article["end_date"])
    # del article["dateDebut"]
    # del article["dateFin"]
    return article


