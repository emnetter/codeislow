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
    get_short_code_from_full_name,
    get_code_full_name_from_short_code
)


def convert_date_to_datetime(date):
    '''
    Convert date object to datetime object
    Arguments: 
        date: date object (dd/mm/YYYY)
    Returns:
        datetime: datetime object (dd/mm/YYYY HH:MM:SS)
    '''
    return datetime.datetime.fromordinal(date.toordinal())


def convert_datetime_to_date(date_time):
    '''
    Convert datetime object to date object
    Arguments: 
        datetime: datetime object (dd/mm/YYYY HH:MM:SS)
    Returns:
        date: date object (dd/mm/YYYY)    
    '''
    date_time.replace(hour=0, minute=0, second=0)
    return date_time


def convert_epoch_to_datetime(epoch):
    """
    Convert epoch (timestamp in seconds) to datetime object
    Arguments: 
        epoch: number of seconds till 1970/01/01
    Returns:
        datetime: datetime object (dd/mm/YYYY HH:MM:SS)    
    """
    return datetime.datetime.utcfromtimestamp(epoch / 1000)


def convert_datetime_to_epoch(date_time):
    """
    Convert datetime object to epoch (timestamp in seconds) 
    Arguments: 
        date_time: datetime object (dd/mm/YYYY HH:MM:SS)
    Returns:
        epoch: number of milliseconds till 1970/01/01
    """
    epoch = datetime.datetime.utcfromtimestamp(0)
    # return date_time - epoch
    return (date_time - epoch).total_seconds() * 1000


def convert_date_to_str(date_time):
    """
    convert date object into string representtation (dd/mm/YYYY)
    Arguments: 
        date_time: datetime object (dd/mm/YYYY HH:MM:SS)
    Returns:
        date_str: "dd/mm/YYYY"
    """
    return datetime.datetime.strftime(date_time[:4], "%d/%m/%Y")


def convert_datetime_to_str(date_time):
    """
    Convert datetime into string format
    Arguments: 
        date_time: datetime object (dd/mm/YYYY HH:MM:SS)
    Returns:
        datetime_str: "dd/mm/YYYY HH:MM:SS"
    """
    return datetime.datetime.strftime(date_time, "%d/%m/%Y %H:%M:%S")


def convert_str_to_datetime(date_time):
    '''
    Convert string format into datetime
    Arguments:
        datetime_str: "dd/mm/YYYY HH:MM:SS"
    Returns:
        date_time: datetime object (dd/mm/YYYY HH:MM:SS)
    '''
    return datetime.datetime.strptime(date_time, "%d/%m/%Y %H:%M:%S")


def return_code_short_and_long(code_name):
    '''
    Get the two version of the code: short and long given a str
    Arguments:
        code_name: str of code name
    Returns:
        short_code: str of the code name in short version
        long_code:  str of the code name in long version
    '''
    if code_name in MAIN_CODELIST.keys():
        return (code_name, MAIN_CODELIST[code_name])
    else:
        short_code = get_short_code_from_full_name(code_name)
        if short_code is None:
            return (None, code_name)
        else:
            return (short_code, code_name)        

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
    #removing HH:MM:SS
    start_date_str = convert_datetime_to_str(start).split(" ")[0]
    end_date_str = convert_datetime_to_str(end).split(" ")[0]
    if start > past_boundary:
        return (301, f"Modifié le {start_date_str}", "yellow")
    if end < future_boundary:
        return (302, "Valable jusqu'au {end_date_str}", "orange")
    if start < past_boundary and end > future_boundary:
        return (204, "Pas de modification", "green")


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
    short_code, long_code = return_code_short_and_long(code_name)
    if short_code is None:
        article = {
            "code_full_name": long_code,
            "code_short_name": short_code,
            "number": article_number,
            "status_code": 404,
            "status": "Le nom du code n'a pas été trouvé",
        }
    else:
        article = {
            "code_full_name": long_code,
            "code_short_name": short_code,
            "number": article_number,
            "status_code": 200,
            "status": "OK",
            "color": "blue"
        }
    article_id = get_article_uid(
        long_code, article_number, headers=get_legifrance_auth(client_id, client_secret)
    )
    if article_id is None:
        article["color"] = "red"
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
    article["status_code"], article["status"], article["color"] = get_validity_status(article["start_date"], article["end_date"], past_year_nb, future_year_nb)
    article["date_debut"] = convert_datetime_to_str(article["start_date"])
    article["date_fin"] = convert_datetime_to_str(article["end_date"])
    del article["dateDebut"]
    del article["dateFin"]
    return article


