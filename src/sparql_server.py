from flask import Flask, jsonify, request
import json
from rdflib import Graph, URIRef, Literal
import sys
from pathlib import Path
import datetime

app = Flask("__name__")

def load_ttls(directory):
    print("Ingesting ttl files".format(datetime.datetime.now()))
    rdf_graph = Graph()
    ttl_path = Path(directory)
    files = ttl_path.glob("*.ttl")
    for f in files:
        with open(f, encoding='utf-8') as input_file:
            print(f)
            rdf_graph.parse(file=input_file, format='turtle')
    return rdf_graph

@app.route("/")
def index():
    return "Hi"


@app.route("/sparql", methods=["POST"])
def sparql():
    query = request.data.decode()
    try:
        res = g.query(query)
        result = {"vars": res.vars, "data": [x for x in res]}
        response = app.response_class(
            response=json.dumps(result),
            status=200,
            mimetype="application/json"
        )
    except ValueError as e:
        response = app.response_class(
            response=json.dumps(e),
            status=500,
            mimetype="application/json"
        )
    return response


if __name__ == "__main__":
    print("Starting at {}".format(datetime.datetime.now()))
    with open("spaql_server.cfg", "r") as f:
        config = json.loads(f.read())
        directory = config.get("directory")
        if directory:
            g = load_ttls(directory)
            print("Ready to server {} triples at {}".format(len(g), datetime.datetime.now()))
        else:
            print("No directory found in .cfg")
            sys.exit(99)
    app.run()