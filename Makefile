PYTHON=.venv/Scripts/python
PIP=.venv/Scripts/python -m pip
STREAMLIT=.venv/Scripts/streamlit
PYTEST=.venv/Scripts/pytest

.PHONY: install run test build-db all

install:
	python -m venv .venv
	$(PIP) install -r requirements.txt

run:
	$(STREAMLIT) run streamlit_app.py

test:
	$(PYTEST)

build-db:
	$(PYTHON) -m app.build_database

all: install build-db run
