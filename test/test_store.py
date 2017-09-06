import json
import operator
import pathlib
import random

import pytest

from bson import ObjectId
from pymongo import MongoClient
from songapi.store import Store

# pylint: disable=redefined-outer-name,missing-docstring

TEST_DATA = pathlib.Path(__file__).parent / 'songs.json'


@pytest.fixture(scope='session')
def test_data():
    with TEST_DATA.open() as fp:
        return json.load(fp)


@pytest.fixture(scope='function')
def db(test_data):
    db_name = 'test_{:08x}'.format(random.getrandbits(32))

    with MongoClient() as mc:
        db_ = mc[db_name]
        for entry in test_data:
            db_.songs.insert(entry)
        try:
            yield db_
        finally:
            mc.drop_database(db_name)


@pytest.fixture(scope='function')
def store(db):
    st = Store(db)
    st.ensure_index()
    return st


# ObjectIds in Mongo are ordered, so it is safe to assume that
# the order of test data matches the one in the DB.

def verify_output(expected, actual):
    assert len(expected) == len(actual)
    for exp, act in zip(expected, actual):
        for k, v in exp.items():
            assert act[k] == v


def test_list_all(store, test_data):
    result = store.list(limit=len(test_data))
    assert len(result) == len(test_data)


def test_list_paging(store, test_data):
    page1 = store.list(limit=2)
    verify_output(test_data[:2], page1)
    last_id = str(page1[-1]['_id'])

    page2 = store.list(after_id=last_id, limit=3)
    verify_output(test_data[2:5], page2)

    last_id = str(page2[-1]['_id'])
    page3 = store.list(after_id=last_id, limit=100)

    verify_output(test_data[5:], page3)

    last_id = page3[-1]['_id']
    assert not store.list(after_id=last_id, limit=1)


def test_add_rating(store):
    song_id = str(store.list(limit=1)[0]['_id'])
    store.add_rating(song_id, 4)
    store.add_rating(song_id, 2)

    output = store.list(limit=1)[0]
    assert output['rating']['4'] == 1
    assert output['rating']['2'] == 1
    assert output['rating']['votes'] == 2


def test_find_by_id(store):
    for song in store.list():
        verify_output([song], [store.find_by_id(song['_id'])])


def test_find_by_id_not_found(store):
    with pytest.raises(store.SongNotFound):
        store.find_by_id(ObjectId())


@pytest.mark.parametrize('level,result',
                         [[None, 10.3236],
                          [9, 9.693],
                          [1, 0]], ids=('all', 'level', 'missing'))
def test_avg(store, level, result):
    assert abs(result - store.get_average_difficulty(level)) < 0.001


def test_search_artist(store):
    result = store.search('youSiCian')
    assert len(result) == 10
    for song in result:
        assert 'yousician' in song['artist'].lower()

    assert len(store.search('fastfinger')) == 1
    assert len(store.search('beatles')) == 0


def test_search_title(store):
    result = store.search('power')
    assert len(result) == 1
    assert 'power' in result[0]['title'].lower()

    # with delimiter
    assert len(store.search('waki')) == 1

    # few words
    assert len(store.search('kennel new')) == 1


def test_search_multiple_fields(store):
    dylan = {'artist': 'Bob Dylan', 'title': 'Lay Lady Lay'}
    gaga = {'artist': 'Lady Gaga', 'title': 'Poker Face'}
    store.insert(dylan)
    store.insert(gaga)

    result = store.search('lady')
    result.sort(key=operator.itemgetter('artist'))
    verify_output([dylan, gaga], result)

    verify_output([gaga], store.search('gaga poker'))
