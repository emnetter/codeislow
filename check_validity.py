#!/usr/bin/env python3
# coding: utf-8
# filename: check_validity.py
"""

Module de vérification du status de l'article

- multiple time_converters:
    - (date <-> datetime)
    - (date,datetime <-> str)
    - (epoch<-> datetime)
- time_delta: définition de nouvelle dates à partir d'un nombre année
- check validity: module qui définit le status de l'article en fonction d'une plage temporelle

"""
from datetime import datetime
import datetime
from dateutil.relativedelta import relativedelta



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

### SPECIALS: plage de temps + status de l'article
def time_delta(operator, year_nb):
    """
    Calculer le différentiel de date selon l'opérator et le nombre d'années
    Arguments
    ---------- 
    operator: str
        chaine de caractère qui représente l'opérateur: - ou +
    year_nb: int
        entier qui représente le nombre d'années
    Return
    -------
    datetime_delta: datetime
        objet datetime représentant la nouvelle date 
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
    
    Arguments
    ---------- 
    operator: str
        chaine de caractère qui représente l'opérateur: - ou +
    year_nb: int
        entier qui représente le nombre d'années
    Return
    -------
    epoch_delta: int
        timestamp/epoch représentant la nouvelle date 
    """
    
    
    return convert_datetime_to_epoch(time_delta(operator, year_nb))

def get_validity_status(start, end, year_before, year_after):
    """
    Verifier la validité de l'article à partir d'une plage de temps

    Arguments
    ---------
    year_before: int
        Nombre d'année avant aujourd'hui
    start: datetime
        Date de création de l'article
    year_after:int
        Nombre d'année après aujourd'hui
    end: datetime 
        Date d'expiration de l'article

    Returns
    --------
    status_code: int
        Un code de status qui s'inspire d'HTTP
    response: str
        Un message de status
    color: str
        Couleur CSS du status: green, yellow, orange, red
    """
    past_boundary = time_delta("-", year_before)
    future_boundary = time_delta("+", year_after)
    if start > past_boundary:
        return (301, "Modifié le {}".format(convert_datetime_to_str(start).split(" ")[0]), "yellow")
    if end < future_boundary:
        return (302, "Valable jusqu'au {}".format(convert_datetime_to_str(end).split(" ")[0]), "orange")
    if start < past_boundary and end > future_boundary:
        return (204, "Pas de modification", "green")

