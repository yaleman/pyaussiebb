project := "aussiebb"

default: checks

test:
    uv run pytest -m 'not network'

# Run mkdocs in watch mode
docs_serve:
    uv run mkdocs serve

lint:
    uv run ruff check {{project}} tests

mypy :
    uv run mypy --strict {{project}} tests

checks: lint mypy test

# run coverage checks and output html
coverage:
    uv run coverage run -m pytest && uv run coverage html && open htmlcov/index.html

build:
    checks
    find . -name ".DS_Store" -exec rm {} \;
    uv build

publish: build
    uv publish