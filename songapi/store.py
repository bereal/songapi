import pymongo
from bson import ObjectId


def _normalize_id(id_):
    if not isinstance(id_, str):
        return id_
    return ObjectId(id_)


class Store:
    class SongNotFound(Exception):
        pass

    def __init__(self, db=None):
        self._col = db.songs

    def find_by_id(self, song_id):
        query = {'_id': _normalize_id(song_id)}
        result = self._col.find_one(query)
        if not result:
            raise self.SongNotFound('Song {} is not found'.format(song_id))

        return result

    def get_average_difficulty(self, level=None):
        raise NotImplementedError

    def search(self, text):
        raise NotImplementedError

    def list(self, after_id=None, limit=20):
        query = {}
        if after_id:
            query['_id'] = {'$gt': _normalize_id(after_id)}

        result = self._col.find(query)
        return list(result.limit(limit) if limit else result)

    def add_rating(self, song_id, rating):
        inc = {
            'rating.{}'.format(rating): 1,
            'rating.votes': 1,
        }
        self._col.update({'_id': _normalize_id(song_id)}, {'$inc': inc})
