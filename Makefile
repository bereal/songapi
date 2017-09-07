DBNAME := songsapi_demo
SEED := test/songs.json
PORT := 5000

test:
	PYTHONPATH=. py.test -sv test/

seed:
	PYTHONPATH=. python songapi/app.py --db-name $(DBNAME) --db-seed $(SEED)

demo:
	PYTHONPATH=. python songapi/app.py --db-name $(DBNAME) --port $(PORT) --debug

dep:
	pip install -r requirements.txt

.PHONY: test seed demo
