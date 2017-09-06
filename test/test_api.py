import json
import unittest.mock as mock
import pytest

from flask import Flask, g
from songapi.api import api

# pylint: disable=redefined-outer-name,missing-docstring

class Client:
    def __init__(self, client):
        self._client = client

    def __getattr__(self, name):
        return getattr(self._client, name)

    def get_json(self, url):
        response = self._client.get(url)
        body = response.data.decode('ascii')
        return json.loads(body)


@pytest.fixture(scope='function')
def app():

    test_app = Flask(__name__)
    test_app.register_blueprint(api, url_prefix='/songs')

    test_app.testing = True
    with test_app.app_context():
        g.store = mock.Mock()
        g.store.ID = int
        yield Client(test_app.test_client())


def test_avg(app):
    g.store.get_average_difficulty.return_value = 5
    response = app.get_json('/songs/avg/difficulty')
    assert response['avg_difficulty'] == 5


def test_avg_for_level(app):
    g.store.get_average_difficulty.return_value = 7
    response = app.get_json('/songs/avg/difficulty?level=9')
    assert response['avg_difficulty'] == 7
    g.store.get_average_difficulty.assert_called_with(9)


def test_avg_wrong_level(app):
    response = app.get('/songs/avg/difficulty?level=cov')
    assert response.status_code == 400


def test_search(app):
    g.store.search.return_value = ['PLACEHOLDER']
    response = app.get_json('/songs/search?message=abcdef')
    assert response == ['PLACEHOLDER']
    g.store.search.assert_called_with('abcdef')


def test_add_rating(app):
    g.store.add_rating.return_value = []
    response = app.post('/songs/rating?song_id=123&rating=4')
    assert response.status_code == 200
    g.store.add_rating.assert_called_with(123, 4)


def test_add_rating_wrong_rating_1(app):
    response = app.post('/songs/rating?song_id=123&rating=abc')
    assert response.status_code == 400
    assert not g.store.add_rating.called


def test_add_rating_wrong_rating_2(app):
    response = app.post('/songs/rating?song_id=123&rating=7')
    assert response.status_code == 400
    assert not g.store.add_rating.called


def test_add_rating_missing_rating(app):
    response = app.post('/songs/rating?song_id=123')
    assert response.status_code == 400
    assert not g.store.add_rating.called


def test_add_rating_wrong_song_id(app):
    response = app.post('/songs/rating?song_id=abc&rating=4')
    assert response.status_code == 400
    assert not g.store.add_rating.called


def test_avg_rating(app):
    g.store.find_by_id.return_value = {
        'rating': {
            'total': 48,
            'votes': 12,
            'min': 3,
            'max': 5,
        }
    }

    response = app.get_json('/songs/avg/rating/123')
    assert response['min'] == 3
    assert response['max'] == 5
    assert response['avg'] == 4
    g.store.find_by_id.assert_called_with(123)


def test_avg_rating_no_rating(app):
    g.store.find_by_id.return_value = {}
    response = app.get_json('/songs/avg/rating/123')
    assert response == {}


def test_avg_rating_wrong_song_id(app):
    response = app.get('/songs/avg/rating/wrong')
    assert response.status_code == 400
    assert not g.store.find_by_id.called
