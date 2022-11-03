#!/usr/bin/env python3
# coding: utf-8
#filename: app.py
"""
Main Bottle app

"""
from bottle import Bottle

from bottle import static_file, request
from jinja2 import Environment, FileSystemLoader
from code_references import CODE_REFERENCE, CODE_REGEX
from codeislow import main

app = Bottle()

environment = Environment(loader=FileSystemLoader("templates/"))

@app.route("/")
def home():
    template = environment.get_template("home.html")
    return template.render()

@app.route("/home")
def accueil():
    template = environment.get_template("home.html")
    return template.render()

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
https://stackoverflow.com/questions/69125397/call-function-with-arguments-from-user-input-in-python3-flask-jinja2-template
https://stackoverflow.com/questions/6036082/call-a-python-function-from-jinja2

@app.route("/upload/", method="POST")
def upload():
    filename = request.args.get('upload')
    past = request.args.get('past')
    future =  request.args.get('future')
    results = yield from main(filename, None, "article_code", past, future)
    template = environment.get_template("results.html")
    return template.render(results = results)

if __name__ == "__main__":
#    if os.environ.get("APP_LOCATION") == "heroku":
#         SSLify(app)
#         app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
#     else:
    app.run(host="localhost", port=8080, debug=True, reloader=True)
