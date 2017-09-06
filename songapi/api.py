from flask import Blueprint, request, g, jsonify, abort


def getarg(name, type_=str, *, default=None, required=False, src=None):
    src = src or request.args
    try:
        arg = request.args[name]
    except KeyError:
        if required:
            abort(400, '{} is required'.format(name))

        return default

    try:
        return type_(arg)
    except:
        abort(400, 'argument {} is malformed'.format(name))


api = Blueprint('songs', __name__)


@api.route('/')
def list_songs():
    limit = getarg('limit', int, default=20)
    after_id = getarg('after_id', g.store.ID)
    return jsonify(g.store.list(after_id=after_id, limit=limit))


@api.route('/avg/difficulty')
def get_avg_difficulty():
    level = getarg('level', int)
    avg = g.store.get_average_difficulty(level)
    return jsonify({'avg_difficulty': avg})


@api.route('/search')
def search():
    message = getarg('message', required=True)
    return jsonify(g.store.search(message))


@api.route('/rating', methods=['POST'])
def add_rating():
    song_id = getarg('song_id', g.store.ID, src=request.form, required=True)
    rating = getarg('rating', int, src=request.form, required=True)
    if not 1 <= rating <= 5:
        abort(400, 'rating must be between 1 and 5')

    g.store.add_rating(song_id, rating)
    return jsonify({})


@api.route('/avg/rating/<song_id>')
def avg_rating(song_id):
    try:
        song_id = g.store.ID(song_id)
    except:
        abort(400, 'malformed song_id')

    song = g.store.find_by_id(song_id)
    rating = song.get('rating', {})
    total = rating.get('total')
    votes = rating.get('votes')
    if total and votes:
        rating['avg'] = float(total) / votes

    return jsonify(rating)
