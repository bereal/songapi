from pymongo import MongoClient, TEXT
from bson import ObjectId


class Store:
    class SongNotFound(Exception):
        pass

    ID = ObjectId

    def __init__(self, db=None):
        self._col = db.songs

    @classmethod
    def _normalize_id(cls, id_):
        if isinstance(id_, cls.ID):
            return id_
        return cls.ID(id_)

    def ensure_index(self):
        self._col.create_index([('title', TEXT), ('artist', TEXT)],
                               background=True)

    def find_by_id(self, song_id):
        query = {'_id': self._normalize_id(song_id)}
        result = self._col.find_one(query)
        if not result:
            raise self.SongNotFound('Song {} is not found'.format(song_id))

        return result

    def list(self, after_id=None, limit=20):
        query = {}
        if after_id:
            query['_id'] = {'$gt': self._normalize_id(after_id)}

        result = self._col.find(query)
        return list(result.limit(limit) if limit else result)

    def add_rating(self, song_id, rating):
        # all the aggregated stats can be calculated on-read,
        # but I anticipate reads to be much more frequent than writes
        update = {
            '$inc': {
                'rating.{}'.format(rating): 1,
                'rating.votes': 1,
                'rating.total': rating,
            },
            '$min': {'rating.min': rating},
            '$max': {'rating.max': rating},
        }
        self._col.update({'_id': self._normalize_id(song_id)}, update)

    AVG_LEVEL_GROUP = {'$group': {'_id': None, 'avg': {'$avg': '$difficulty'}}}

    def get_average_difficulty(self, level=None):
        pipeline = []
        if level:
            pipeline.append({'$match': {'level': level}})

        pipeline.append(self.AVG_LEVEL_GROUP)
        result = next(self._col.aggregate(pipeline), {})
        return result.get('avg', 0)

    def search(self, text):
        query = {'$text': {'$search': text}}
        return list(self._col.find(query, { 'score': {'$meta': 'textScore'} }))

    def insert(self, song):
        self._col.insert(song)
