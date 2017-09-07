import argparse
import json
import sys

from flask import Flask, request, g, jsonify, redirect
from flask_pymongo import PyMongo
from werkzeug.exceptions import HTTPException
from werkzeug.routing import RequestRedirect

from songapi.api import api, list_songs
from songapi.store import Store, SongNotFound, MongoEncoder


class App(Flask):
    def handle_exception(self, err):
        try:
            raise err
        except SongNotFound:
            status = 404
            msg = 'Song is not found'
        except:
            status = 500
            msg = str(err)

        response = jsonify(error=msg)
        response.status_code = status
        return response

    def handle_http_exception(self, err):
        response = jsonify(error = err.description)
        response.status_code = err.code
        return response


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--debug', action='store_true', default=False)
    ap.add_argument('--port', type=int, default=5000)
    ap.add_argument('--db-init', action='store_true', default=False,
                    help='initialize the db and exit')
    ap.add_argument('--db-seed', default=None,
                    help='seed database and exit', metavar='FILENAME')
    ap.add_argument('--db-name', default='songsapi_demo')

    return ap.parse_args()


def main():
    args = parse_args()

    app = App(__name__)
    app.config['MONGO_DBNAME'] = args.db_name
    app.json_encoder = MongoEncoder
    mongo = PyMongo(app)

    if args.db_init:
        with app.app_context():
            Store(mongo.db).init()
        sys.exit(0)

    if args.db_seed:
        with app.app_context():
            with open(args.db_seed) as fp:
                Store(mongo.db).seed(json.load(fp))
        sys.exit(0)

    @app.before_request
    def create_store():
        g.store = Store(mongo.db)

    app.url_map.strict_slashes = False
    app.register_blueprint(api, url_prefix='/songs')
    app.run(debug=args.debug, port=args.port)


if __name__ == '__main__':
    main()
