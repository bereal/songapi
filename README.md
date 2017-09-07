# songapi

### Requirements and dependencies

 * Python 3
 * pip
 * MongoDB (tested with 3.4.3)
 * pymongo (tested with 3.4.0)
 * Flask (tested with 0.12.1)
 * Flask-PyMongo (tested with 0.5.1)
 * Py.test for testing (tested with 3.0.7)

### Installation and running

To install the dependencies (assuming that all Python3 and pip are installed, and permission are granted, e.g. withing a virtualenv or a conda):

    make dep

To run all the tests:

    make test

The storage layer is tested in integration with a running mongo instance. If Mongo is not running, the corresponding tests are automatically skipped. A new temporarily DB is created for each test to ensure their independence. The API layer is tested using the standard Flask means.

To initialize the database, create the indices and seed the test data (run once, assuming the mongod is running on the same host on the default port):

    make seed

To start the server in the debug mode, port 5000:

    make demo


### Quick checks

    > curl localhost:5000/songs/avg/difficulty
    {
      "avg_difficulty": 10.323636363636364
    }

    > curl 'localhost:5000/songs/avg/difficulty?level=13'
    {
      "avg_difficulty": 14.096
    }

    > curl 'localhost:5000/songs/search?message=fastfinger
    [
      {
        "_id": "59b102bdf29a582985a25a8e",
        "artist": "Mr Fastfinger",
        "difficulty": 15,
        "level": 13,
        "released": "2012-05-11",
        "score": 0.75,
        "title": "Awaki-Waki"
      }
    ]

    > export song_id=`curl localhost:5000/songs | jq -r '.[0]._id'`
    > curl -XPOST "localhost:5000/songs/rating?song_id=${song_id}&rating=5"
    > curl -XPOST "localhost:5000/songs/rating?song_id=${song_id}&rating=4"
    > curl "localhost:5000/songs/avg/rating/${song_id}"
    {
      "4": 1,
      "5": 1,
      "avg": 4.5,
      "max": 5,
      "min": 4,
      "total": 9,
      "votes": 2
    }
