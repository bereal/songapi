import json
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
    return Store(db)


# ObjectIds in Mongo are so it is safe to assume that
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


def test_add_rating(store, test_data):
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
