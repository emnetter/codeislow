#!usr/bin/env python
import pytest
import os
from dotenv import load_dotenv
from pathlib import Path
from bottle import FileUpload

from bottle import Bottle
from bottle import request, static_file, template, HTTPError, run
import jinja2

from parsing import parse_doc
from matching import match_code_and_articles, gen_matching_results
from checking import get_article

def upload_document(upload, past, future):
    '''
    Téléverser le document le stocker temporairement
    Arguments:
        document: a file 
    Yield:
        article trouvé
    '''
    save_path = Path.cwd() / Path("tmp")
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    file_path = "{path}/{file}".format(path=save_path, file=upload.filename)
    upload.save(file_path, overwrite="true")
    file_size = os.stat(file_path).st_size
    if file_size > 2000000:
        raise Exception("Fichier trop lourd: la taille du fichier doit être < à 2Mo")
    
    full_text = parse_doc(file_path)
    load_dotenv()
    client_id = os.getenv("API_KEY")
    client_secret = os.getenv("API_SECRET")
    try:
        for code, code_name, article in gen_matching_results(full_text):
            
            yield get_article(code_name, article, client_id, client_secret, past_year_nb=past, future_year_nb=future)
    except Exception as e:
        return (501, e, None, None)
    # os.remove(file_path)
    # return found_articles


app = Bottle()

@app.route("/")
def root():
    return static_file("home.html", root="./")

@app.route("/cgu")
def cgu():
    return static_file("cgu.html", root="./")

@app.route("/code_list")
def code_list():
    return static_file("code_list.html", root="./")

@app.route("/upload", method="POST")
def analyse_document():
    upload = request.files.get("upload")
    past = request.get("user_past")
    future = request.get("user_future")
    # try:
    #     article_found = upload_document(upload)
    # except Exception as e:
    #     return f'<html><body><p>{e}</p></body></html>'
    document_name = upload.filename.split("/")[-1]
    # environment = jinja2.Environment()
    # template = environment.from_string(matching_results)
    # return template.render(filename=document_name, code_articles_found=article_found)
    yield """<!DOCTYPE html>
    <head>
    <title> Code is low</title>
    <link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    
    </head>    
    <body>
    <div class="w3-container w3-blue-grey">
        <h1> Code is low</h1>
    </div>
    <div class="w3-panel w3-leftbar w3-sand w3-xxlarge">
        <p class="w3-center">
            <i>L'analyse est en cours. Veuillez patienter... </i>
        </p>
        <p class="w3-center">
            <i class="fa fa-refresh w3-spin" style="font-size:64px"></i>
        </p>
    </div>
    <div class="container w3-margin responsive">
    <table class="w3-table-all">
    <tr>
    <th>#</th>
    <th>Code</th>
    <th>Article</th>
    <th>Statut</th>
    <th>Texte</th>
    </tr>"""
    for i,result in enumerate(upload_document(upload, past, future)):
        if isinstance(result, list):
            
            return f"""<tr>
                            <td>Error: {result[0]}</td>
                            <td>{result[1]}</td>
                            <td></td>
                            <td></td>
                        <td class="w3-col"></td>
                    </tr>
                    """     
        if result["status_code"] == 204:
            css_class = "w3-green"
        elif result["status_code"] == 301:
            css_class = "w3-yellow"
        elif result["status_code"] == 302:
            css_class = "w3-orange"
        else:
            css_class = "w3-red"
        if result["status_code"] == 404:
            yield f"""<tr>
                            <td>{i+1}</td>
                            <td>{result['code_full_name']}</td>
                            <td>{result['number']}</td>
                            <td><span class="w3-tag {css_class}">{result['status']}</span></td>
                        <td class="w3-col"></td>
                    </tr>"""+f"""</table></div>
    <div class="container">
    <div class='w3-card w3-margin w3-pale-green'>
        <p class="w3-margin"><b>{i+1}</b> articles detectés dans le document {document_name}</p>
    </div>
     <div class="w3-bar w3-center">
        <a href="/" class="w3-button w3-red"><i class="fa fa-home"></i>Retour</a>
        <a href="/export" class="w3-button w3-black w3-disabled"><i class="fa fa-download"></i>Enregister en csv</a>
        <a href="/https://github.com/emnetter/codeislow/issues/new" class="w3-button w3-blue w3-disabled"><i class="fa fa-download"></i>Poser une question</a>
    </div> 
    </div>
    </html>"""
        else:
            yield f"""<tr>
            <td>{i+1}</td>
            <td>{result['code_full_name']}</td>
            <td><a href="{result['url']}">{result['number']}</a></td>
            <td>
            
            <span class="w3-tag {css_class}">{result['status']}</span>

            </td>
            <td width="50%">{result['texte']} <a href="{result['url']}">...</a></td></span>
            </tr>"""            
    yield f"""</table></div>
    <div class="container">
    <div class='w3-card w3-margin w3-pale-green'>
        <p class="w3-margin"><b>{i+1}</b> articles detectés dans le document {document_name}</p>
    </div>
     <div class="w3-bar w3-center">
        <a href="/" class="w3-button w3-red"><i class="fa fa-home"></i>Retour</a>
        <a href="/export" class="w3-button w3-black w3-disabled"><i class="fa fa-download"></i>Enregister en csv</a>
        <a href="/https://github.com/emnetter/codeislow/issues/new" class="w3-button w3-blue w3-disabled"><i class="fa fa-download"></i>Poser une question</a>
    </div> 
    </div>
    </html>"""
if __name__=="__main__":
    app.run(host="localhost", port=8080, debug=True, reloader=True)
