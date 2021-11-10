#!/usr/bin/env python3

import re
import docx
import requests
import json
import datetime
import os
from dotenv import load_dotenv, find_dotenv
from odf import text, teletype
from odf.opendocument import load
from pathlib import Path
from bottle import route, request, static_file, run, template

# Tri des paragraphes du texte pour retenir seulement ceux
# faisant référence à un "article"
def paragraphs_selector(paragraphs):
    paragraphs_to_test = []
    article_detector = re.compile(r"(^.*(?:article|art\.).*$)", flags=re.I | re.M)
    for paragraph in paragraphs:
        paragraphs_to_add = article_detector.findall(paragraph)
        if paragraphs_to_add != []:
            paragraphs_to_test.append(paragraphs_to_add)
    return paragraphs_to_test


# Les paragraphes à tester sont confrontés aux expressions régulières de chaque code
def text_detector(paragraphs_to_test):
    for code in main_codelist:
        code_results[code] = []
    for code in main_codelist:
        code_detecteur = re.compile(codes_regex[code], re.I)
        for paragraph in paragraphs_to_test:
            for element in paragraph:
                results = code_detecteur.findall(element)
                for group in results:
                    for match in group:
                        if (
                            match != ""
                            and reformat_results(match) not in code_results[code]
                        ):
                            code_results[code].append(reformat_results(match))
    return code_results


# Permet de visualiser les articles de code trouvés dans le terminal
def results_printer(code_results):
    for code in main_codelist:
        if code_results[code] != []:
            print(f"Textes du {main_codelist[code]} identifiés:")
            print((code_results[code]))


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


# Authentification sur Légifrance à l'aide de secrets conservés dans .env
def legifrance_auth():
    TOKEN_URL = "https://oauth.piste.gouv.fr/api/oauth/token"

    load_dotenv(find_dotenv())
    CLIENT_ID = os.environ.get("CLIENT_ID")
    CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

    res = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "openid",
        },
    )
    token = res.json()
    access_token = token["access_token"]
    return access_token


# Pour chaque article de code, Légifrance est interrogé et renvoie un dico JSON
def trouve_article(idtext, idarticle):

    data = {"id": idtext, "num": idarticle}

    response = requests.post(
        "https://api.piste.gouv.fr/dila/legifrance-beta/"
        "lf-engine-app/consult/getArticleWithIdAndNum",
        headers=headers,
        json=data,
    )

    dico = json.loads(response.text)
    return dico["article"]


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
}
codes_API = {
    "CCIV": "LEGITEXT000006070721",
    "CPRCIV": "LEGITEXT000006070716",
    "CPCE": "LEGITEXT000025024948",
    "CCOM": "LEGITEXT000005634379",
    "CTRAV": "LEGITEXT000006072050",
    "CMF": "LEGITEXT000006072026",
    "CCONSO": "LEGITEXT000006069565",
    "CGI": "LEGITEXT000006069577",
    "CPEN": "LEGITEXT000006070719",
    "CPP": "LEGITEXT000006071154",
    "CPI": "LEGITEXT000006069414",
    "CASSUR": "LEGITEXT000006073984",
    "CSI": "LEGITEXT000025503132",
}

reg_beginning = {
    "UNIVERSAL": r"((?:L\.?|R\.?|A\.?|D\.?)?\s*\d+-?\d*-?\d*)\s*(?:alinéa|al\.)?\s*\d*\s*"
    r"(?:,\s*((?:L\.?|R\.?|A\.?|D\.?)?\s*\d+-?\d*-?\d*)\s*(?:alinéa|al\.)?\s*\d*\s*"
    r"(?:,\s*((?:L\.?|R\.?|A\.?|D\.?)?\s*\d+-?\d*-?\d*)\s*(?:alinéa|al\.)?\s*\d*\s*"
    r"(?:,\s*((?:L\.?|R\.?|A\.?|D\.?)?\s*\d+-?\d*-?\d*)\s*(?:alinéa|al\.)?\s*\d*\s*)*)*)*"
    r"(?:et\s*((?:L\.?|R\.?|A\.?|D\.?)?\s*\d+-?\d*-?\d*)\s*(?:alinéa|al\.)?\s*\d*\s*)*",
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
    "CSI": r"\s*(?:du Code de la sécurité intérieure|CSI|du CSI)"
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
    "CSI" : reg_beginning["UNIVERSAL"] + reg_ending["CSI"],
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

    code_results = dict()
    articles_not_found.clear()
    articles_recently_modified.clear()
    articles_changing_soon.clear()
    articles_without_event.clear()

    for code in main_codelist:
        code_results[code] = []

    # L'utilisateur définit sur quelle période la validité de l'article est testée
    user_years = request.forms.get("user_years")
    # L'utilisateur upload son document, il est enregistré provisoirement
    upload = request.files.get("upload")
    if upload is None:
        return "Pas de fichier"
    global name, ext
    name, ext = os.path.splitext(upload.filename)
    if ext not in (".odt", ".docx"):
        return "File extension not allowed."
    save_path = Path.cwd() / Path("tmp")
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    file_path = "{path}/{file}".format(path=save_path, file=upload.filename)
    upload.save(file_path, overwrite="true")

    # Le document DOCX ou ODT est transformé en liste de paragraphes
    paragraphsdoc = []

    yield "<h3> Début de l'analyse du texte. Veuillez patienter... </h3>"

    if ext == ".docx":
        document = docx.Document(file_path)
        for i in range(len(document.paragraphs)):
            paragraphsdoc.append(document.paragraphs[i].text)

    elif ext == ".odt":
        document = load(file_path)
        texts = document.getElementsByType(text.P)
        for i in range(len(texts)):
            paragraphsdoc.append(teletype.extractText(texts[i]))

    # Suppression du fichier utilisateur, devenu inutile

    os.remove(file_path)

    # Mise en oeuvre des expressions régulières
    paragraphs_to_test = paragraphs_selector(paragraphsdoc)

    code_results = text_detector(paragraphs_to_test)
    results_printer(code_results)

    # Définition des bornes de la période déclenchant une alerte
    # si l'article a été modifié / va être modifié
    past_reference = (
        datetime.datetime.now() - datetime.timedelta(days=float(user_years) * 365)
    ).timestamp() * 1000
    future_reference = (
        datetime.datetime.now() + datetime.timedelta(days=float(user_years) * 365)
    ).timestamp() * 1000

    for code in code_results:
        yield "<p> " + "Analyse des textes du " + main_codelist[code] + "... </p>"
        for result in code_results[code]:
            donnees_article = trouve_article(idtext=codes_API[code], idarticle=result)
            if donnees_article is None:
                articles_not_found.append(
                    "Article " + result + " du " + main_codelist[code] + " non trouvé"
                )
            else:
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
                        "La version actuelle de l'article"
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
            "user_years": user_years,
        },
    )


# Corps du programme

if __name__ == "__main__":

    access_token = legifrance_auth()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

if os.environ.get("APP_LOCATION") == "heroku":
    run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
else:
    run(host="localhost", port=8080, debug=True)
