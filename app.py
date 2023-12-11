#!/usr/bin/env python3
# coding: utf-8
#filename: app.py
"""
Main Bottle app

"""
import os
import json

from bottle import Bottle
from bottle import request, static_file
from jinja2 import Environment, FileSystemLoader
from code_references import CODE_REFERENCE, CODE_REGEX
from codeislow import main, load_result
from result_templates import start_results, end_results

app = Bottle()

environment = Environment(loader=FileSystemLoader("templates/"))

@app.route("/")
def home():
    template = environment.get_template("home.html")
    return template.render(code_names=list(CODE_REFERENCE.items()))


@app.route("/cgu/")
def cgu():
    template = environment.get_template("cgu.html")
    return template.render()

@app.route("/about/")
def about():
    template = environment.get_template("about.html")
    return template.render()

@app.route("/codes/")
def codes():
    code_full_list = []
    for short_code, long_code in CODE_REFERENCE.items():
        regex_c = CODE_REGEX[short_code]
        regex = f"<code>{regex_c}</code>"
        comment = """<a href="" class="badge badge-pill badge-primary">?</a>"""
        code_full_list.append((long_code, short_code, regex, comment))
    template = environment.get_template("codes.html")
    return template.render(codes_full_list=code_full_list)

# @app.route('/ajax')
# def ajax():
#     template = environment.get_template("results.html")
#     return template.render('results.html',
#                            result=result)
#https://stackoverflow.com/questions/69125397/call-function-with-arguments-from-user-input-in-python3-flask-jinja2-template
#https://stackoverflow.com/questions/6036082/call-a-python-function-from-jinja2

@app.route("/upload/", method="POST")
def upload():
    upload = request.files.get('upload')
    name, ext = os.path.splitext(upload.filename)
    
    if ext not in ('.doc','.docx','.odt', '.pdf'):
        return 'Le format du fichier est incorrect'
    file_path = os.path.join("tmp", upload.filename)
    upload.save(file_path)
    past = int(request.forms.get('user_past'))
    future =  int(request.forms.get('user_future'))
    selected_codes = [short_name for short_name in CODE_REFERENCE.keys() if request.forms.get(short_name) is not None]
    if len(selected_codes) == 0: 
        selected_codes = None
    yield start_results
    for row in load_result(file_path, None, "article_code", past, future):
        yield row
    #     row = f'''
    #         <tr scope="row"><a href='{article["url"]}'>{article["code"]} - {article["article"]}</a></tr>
    #         <tr>{article["status"]}</tr>
    #         <tr>{article["texte"]}</tr>
    #         <tr></tr>
    #     '''
    # yield 
        
    yield end_results
    
if __name__ == "__main__":
#    if os.environ.get("APP_LOCATION") == "heroku":
#         SSLify(app)
#         app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
#     else:
    app.run(host="localhost", port=8080, reloader=True)
