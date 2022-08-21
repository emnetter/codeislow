#!/usr/bin/env python3

import datetime
import json
import os
import re
import sys
import time
from pathlib import Path

import docx
import requests
from PyPDF2 import PdfReader
from bottle import route, request, static_file, run, template
from dotenv import load_dotenv, find_dotenv
from odf import text, teletype
from odf.opendocument import load
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


# Authentification sur Légifrance à l'aide de secrets conservés dans .env
def legifrance_auth():
    token_url = "https://oauth.piste.gouv.fr/api/oauth/token"

    load_dotenv(find_dotenv())
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")

    res = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "openid",
        },
    )
    response = res.json()
    token = response["access_token"]
    return token

def spaces_remover(string):
    return re.sub(" {2,}", " ", string)

# Ouverture du fichier utilisateur
def file_opener(ext, file_path):
    article_detector = re.compile(r"(^.*(?:article|art\.).*$)", flags=re.I | re.M)
    paragraphsdoc = []
    if ext == ".docx":
        yield "<h5> Le fichier DOCX est actuellement parcouru. </h5>"
        document = docx.Document(file_path)
        for i in range(len(document.paragraphs)):
            paragraph = document.paragraphs[i].text
            if article_detector.search(paragraph) is not None:
                paragraphsdoc.append(paragraph)
    elif ext == ".odt":
        yield "<h5> Le fichier ODT est actuellement parcouru. </h5>"
        document = load(file_path)
        texts = document.getElementsByType(text.P)
        for i in range(len(texts)):
            paragraph = teletype.extractText(texts[i])
            if article_detector.search(paragraph) is not None:
                paragraphsdoc.append(paragraph)
    elif ext == ".pdf":
        yield "<h5> Le fichier PDF est actuellement parcouru. </h5>"
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = (page.extract_text())
            if article_detector.search(page_text) is not None:
                paragraphsdoc.append(page_text)
    complete_text = spaces_remover(" ".join(paragraphsdoc))
    return complete_text


# Les paragraphes à tester sont confrontés à l'expression régulière de chaque code
def code_detector(code, string):
    # ajouter un simple match reg-ending pour commencer
    detector = re.compile(codes_regex[code], re.I)
    detected = detector.findall(string)
    detectedlist = list(sum(detected, ()))
    cleanlist = []
    for element in detectedlist:
        if element != "" and reformat_results(element) not in cleanlist:
            cleanlist.append(reformat_results(element))
    sortedlist = sorted(cleanlist)
    return sortedlist


# Les numéros d'articles du texte sont reformatés pour en retirer certains
# caractères (espace, espace insécable, point) qui empêchent la recherche Légifrance
def reformat_results(result):
    newresult = ""
    result = result.replace("\xa0", " ")
    if (result[0]).isdigit():
        return result
    else:
        for char in result:
            if char != "." and char != " ":
                newresult = newresult + char
    return newresult


# Recherche sur Légifrance de l'identifiant unique de l'article
def get_article_id(article_number, code_name):
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
                {"facette": "NOM_CODE", "valeurs": [code_name]},
                {"facette": "DATE_VERSION", "singleDate": today},
            ],
            "pageNumber": 1,
            "pageSize": 10,
            "operateur": "ET",
            "sort": "PERTINENCE",
            "typePagination": "ARTICLE",
        },
        "fond": "CODE_DATE",
    }

    response = session.post(
        "https://api.piste.gouv.fr/dila/legifrance-beta/lf-engine-app/search",
        headers=headers,
        json=data,
    )

    article_informations = json.loads(response.text)
    if not article_informations["results"]:
        return None
    else:
        article_id = article_informations["results"][0]["sections"][0]["extracts"][0][
            "id"
        ]
        # print("return sera ", article_id)
        return article_id


# A partir de l'identifiant unique, rapatriement du contenu de l'article
def get_article_content(article_id):
    data = {"id": article_id}

    response = session.post(
        "https://api.piste.gouv.fr/dila/legifrance-beta/lf-engine-app/consult/getArticle",
        headers=headers,
        json=data,
    )

    article_dictionary = json.loads(response.text)
    return article_dictionary["article"]


# Légifrance utilise des dates au format Epoch qu'il faut convertir au format classique
def epoch_to_date(epoch):
    converted = datetime.datetime(1970, 1, 1) + datetime.timedelta(
        seconds=(epoch / 1000)
    )
    return converted


# Initialisation du programme


main_codelist = {
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
}

reg_beginning = {
    "UNIVERSAL": r"((?:L\.?|R\.?|A\.?|D\.?)?\s*\d+-?\d*-?\d*),?\s*(?:alinéa|al\.)?\s*\d*\s?°?\s*"
                 r"(?:,\s*((?:L\.?|R\.?|A\.?|D\.?)?\s*\d+-?\d*-?\d*),?\s*(?:alinéa|al\.)?\s*\d*\s?°?\s*"
                 r"(?:,\s*((?:L\.?|R\.?|A\.?|D\.?)?\s*\d+-?\d*-?\d*),?\s*(?:alinéa|al\.)?\s*\d*\s?°?\s*"
                 r"(?:,\s*((?:L\.?|R\.?|A\.?|D\.?)?\s*\d+-?\d*-?\d*),?\s*(?:alinéa|al\.)?\s*\d*\s?°?\s*)*)*)*"
                 r"(?:et\s*((?:L\.?|R\.?|A\.?|D\.?)?\s*\d+-?\d*-?\d*),?\s*(?:alinéa|al\.)?\s*\d*\s?°?\s*)*"
                 r"(?:et s\.|et suivants)?",
}

reg_ending = {
    "CCIV": r"\s*(?:du Code civil|C\. civ\.)",
    "CPRCIV": r"\s*(?:du Code de procédure civile|C\. pr\. civ\.|CPC|du CPC)",
    "CCOM": r"\s*(?:du Code de commerce|C\. com\.)",
    "CTRAV": r"\s*(?:du Code du travail|C\. trav\.)",
    "CPI": r"\s*(?:du Code de la propriété intellectuelle|CPI|C\. pr\. int\.|du CPI)",
    "CPEN": r"\s*(?:du Code pénal|C\. pén\.)",
    "CPP": r"\s*(?:du Code de procédure pénale|du CPP|CPP)",
    "CASSUR": r"\s*(?:du Code des assurances|C\. assur\.)",
    "CCONSO": r"\s*(?:du Code de la consommation|C\. conso\.)",
    "CSI": r"\s*(?:du Code de la sécurité intérieure|CSI|du CSI)",
    "CSP": r"\s*(?:du Code de la santé publique|C\. sant\. pub\.|CSP|du CSP)",
    "CSS": r"\s*(?:du Code de la sécurité sociale|C\. sec\. soc\.|CSS|du CSS)",
    "CESEDA": r"\s*(?:du Code de l'entrée et du séjour des étrangers et du droit d'asile|CESEDA|du CESEDA)",
    "CGCT": r"\s*(?:du Code général des collectivités territoriales|CGCT|du CGCT)",
}

codes_regex = {
    "CCIV": reg_beginning["UNIVERSAL"] + reg_ending["CCIV"],
    "CPRCIV": reg_beginning["UNIVERSAL"] + reg_ending["CPRCIV"],
    "CCOM": reg_beginning["UNIVERSAL"] + reg_ending["CCOM"],
    "CTRAV": reg_beginning["UNIVERSAL"] + reg_ending["CTRAV"],
    "CPI": reg_beginning["UNIVERSAL"] + reg_ending["CPI"],
    "CPEN": reg_beginning["UNIVERSAL"] + reg_ending["CPEN"],
    "CPP": reg_beginning["UNIVERSAL"] + reg_ending["CPP"],
    "CASSUR": reg_beginning["UNIVERSAL"] + reg_ending["CASSUR"],
    "CCONSO": reg_beginning["UNIVERSAL"] + reg_ending["CCONSO"],
    "CSI": reg_beginning["UNIVERSAL"] + reg_ending["CSI"],
    "CSP": reg_beginning["UNIVERSAL"] + reg_ending["CSP"],
    "CSS": reg_beginning["UNIVERSAL"] + reg_ending["CSS"],
    "CESEDA": reg_beginning["UNIVERSAL"] + reg_ending["CESEDA"],
    "CGCT": reg_beginning["UNIVERSAL"] + reg_ending["CGCT"],
}

code_results = {}
articles_not_found = []
articles_recently_modified = []
articles_changing_soon = []
articles_without_event = []

for code in main_codelist:
    code_results[code] = []


# Affichage de la page web d'accueil
@route("/")
def root():
    return static_file("index.html", root=".")


# Actions à effectuer à l'upload du document de l'utilisateur
@route("/upload", method="POST")
def do_upload():
    load_dotenv(find_dotenv())
    password = os.environ.get("PASSWORD")
    user_password = request.forms.get("password")
    if user_password != password:
        yield "Mot de passe incorrect"
        sys.exit()
    code_results = dict()
    articles_not_found.clear()
    articles_recently_modified.clear()
    articles_changing_soon.clear()
    articles_without_event.clear()

    for code in main_codelist:
        code_results[code] = []
    # L'utilisateur définit sur quelle période la validité de l'article est testée
    user_past = request.forms.get("user_past")
    user_future = request.forms.get("user_future")
    # L'utilisateur upload son document, il est enregistré provisoirement
    upload = request.files.get("upload")
    if upload is None:
        yield "Pas de fichier"
        sys.exit()
    name, ext = os.path.splitext(upload.filename)
    if ext not in (".odt", ".docx", ".pdf"):
        yield "Extension incorrecte"
        sys.exit()
    save_path = Path.cwd() / Path("tmp")
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    file_path = "{path}/{file}".format(path=save_path, file=upload.filename)
    upload.save(file_path, overwrite="true")

    yield "<h3> Analyse en cours. Veuillez patienter... </h3>"

    cleantext = yield from file_opener(ext, file_path)

    # Suppression du fichier utilisateur, devenu inutile

    #    os.remove(file_path)

    # Mise en oeuvre des expressions régulières
    yield "<h5> Les différents codes de droit français sont recherchés. </h5>"
    for code in main_codelist:
        code_results[code] = code_detector(code, cleantext)

    # Définition des bornes de la période déclenchant une alerte
    # si l'article a été modifié / va être modifié
    past_reference = (
                             datetime.datetime.now() - datetime.timedelta(days=float(user_past) * 365)
                     ).timestamp() * 1000
    future_reference = (
                               datetime.datetime.now() + datetime.timedelta(days=float(user_future) * 365)
                       ).timestamp() * 1000

    # Analyse au regard des dates d'entrée en vigueur et de fin de l'article
    for code in code_results:
        if code_results[code]:
            yield "<h4> " + "La base Légifrance est interrogée : textes du " + main_codelist[
                code
            ] + "... </h4>"
        for result in code_results[code]:
            yield "<small> " + "Article " + result + "...  </small>"
            article_id = get_article_id(
                article_number=result, code_name=main_codelist[code]
            )
            if article_id is None:
                articles_not_found.append(
                    "Article " + result + " du " + main_codelist[code] + " non trouvé"
                )
            else:
                donnees_article = get_article_content(article_id)
                date_debut = donnees_article["dateDebut"]
                date_fin = donnees_article["dateFin"]
                if date_debut < past_reference and date_fin > future_reference:
                    articles_without_event.append(
                        "Article " + result + " du " + main_codelist[code]
                    )
                if date_debut > past_reference:
                    articles_recently_modified.append(
                        "L'article "
                        + result
                        + " du "
                        + main_codelist[code]
                        + " a été modifié le "
                        + str(epoch_to_date(date_debut))
                    )
                if date_fin < future_reference:
                    articles_changing_soon.append(
                        "La version actuelle de l'article "
                        + result
                        + " du "
                        + main_codelist[code]
                        + " n'est valable que jusqu'au "
                        + str(epoch_to_date(date_fin))
                    )
    # Utilisaton d'un template Bottle pour afficher les résultats
    yield template(
        "results",
        **{
            "articles_not_found": articles_not_found,
            "articles_recently_modified": articles_recently_modified,
            "articles_changing_soon": articles_changing_soon,
            "articles_without_event": articles_without_event,
            "user_past": user_past,
            "user_future": user_future,
        },
    )


# Corps du programme

if __name__ == "__main__":
    today = int(time.time() * 1000)

    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    access_token = legifrance_auth()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

if os.environ.get("APP_LOCATION") == "heroku":
    run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
else:
    run(host="localhost", port=8080, debug=True)
