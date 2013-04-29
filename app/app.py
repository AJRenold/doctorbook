#! /usr/local/bin/python

import os
import flask
from flask import (
    Flask,
    request,
    jsonify,
    Response,
    make_response
)
import json

# our tools
from parse_text import ParseTextForWiki

app = Flask(__name__)
app.debug = True

@app.route('/')
def index():
    """render index.html template"""
    return flask.render_template('index.html')

@app.route('/search/', methods=['POST'])
def search_api():

    if request.method == 'POST':

        app.logger.debug('hit')

        text = request.form['text']
        wikis = ParseTextForWiki(text)
        df = wikis.get_wiki_df()
        
        df = [{k:df.values[i][v] for v,k in enumerate(df.columns)} for i in range(len(df)) ]

        return(jsonify(results=df))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run()
