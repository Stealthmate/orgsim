check:
    pre-commit run --all-files --verbose
    uv run mypy --strict orgsim

test:
    uv run pytest tests

run:
    uv run python3 -m orgsim.main