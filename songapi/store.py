import json
from pymongo import MongoClient, TEXT
from bson import ObjectId


class MongoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)

        return super().default(o)


class SongNotFound(Exception):
    pass


class Store:
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
                               background=True, name='songs_text')

    init = ensure_index

    def seed(self, data):
        """Populate the DB from a file
        """
        self.init()
        for song in data:
            self._col.insert(song)

    def find_by_id(self, song_id):
        """Find a song or raise SongNotFound
        """
        query = {'_id': self._normalize_id(song_id)}
        result = self._col.find_one(query)
        if not result:
            raise SongNotFound(song_id)

        return result

    def list(self, after_id=None, limit=20):
        """List the songs with pagination
        after_id is the last song of the previous page
        (ObjectId's are ordered)
        """
        query = {}
        if after_id:
            query['_id'] = {'$gt': self._normalize_id(after_id)}

        result = self._col.find(query)
        return list(result.limit(limit) if limit else result)

    def add_rating(self, song_id, rating):
        """Save a rating vote for the song
        """
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
        updated = self._col.update({'_id': self._normalize_id(song_id)}, update)
        if not updated['nModified']:
            raise SongNotFound

    AVG_LEVEL_GROUP = {'$group': {'_id': None, 'avg': {'$avg': '$difficulty'}}}

    def get_average_difficulty(self, level=None):
        pipeline = []
        if level:
            pipeline.append({'$match': {'level': level}})

        pipeline.append(self.AVG_LEVEL_GROUP)
        result = next(self._col.aggregate(pipeline), {})
        return result.get('avg', 0)

    def search(self, text):
        """Search songs by text in title and artist;
        the text index existence is assumed
        """
        query = {'$text': {'$search': text}}
        return list(self._col.find(query, { 'score': {'$meta': 'textScore'} }))

    def insert(self, song):
        self._col.insert(song)
