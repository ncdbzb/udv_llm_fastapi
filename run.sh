#!/bin/bash

poetry run alembic upgrade head

poetry run python3 main.py