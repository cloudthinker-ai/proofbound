PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: install check rust-check python-check wheel sdist package-check examples audit bench

install:
	@test -x $(BIN)/python || uv venv --python $(PYTHON) $(VENV)
	uv pip install --python $(BIN)/python -r requirements-dev.txt
	VIRTUAL_ENV="$(CURDIR)/$(VENV)" PATH="$(CURDIR)/$(BIN):$$PATH" $(BIN)/maturin develop --locked --manifest-path bindings/python/Cargo.toml

bench:
	VIRTUAL_ENV="$(CURDIR)/$(VENV)" PATH="$(CURDIR)/$(BIN):$$PATH" $(BIN)/maturin develop --release --locked --manifest-path bindings/python/Cargo.toml
	$(BIN)/python scripts/bench_python.py $(BENCH_ARGS)

check: rust-check python-check examples

rust-check:
	cargo fmt --check
	cargo clippy --locked --all-targets --all-features -- -D warnings
	cargo test --locked --all-targets

python-check:
	$(BIN)/ruff check --config bindings/python/pyproject.toml bindings/python/python bindings/python/tests examples/python scripts
	$(BIN)/ruff format --check --config bindings/python/pyproject.toml bindings/python/python bindings/python/tests examples/python scripts
	$(BIN)/python -m mypy bindings/python/python/gdp examples/python
	$(BIN)/python -m pyrefly check --preset default --python-interpreter-path $(BIN)/python bindings/python/python/gdp examples/python
	$(BIN)/python -m pytest bindings/python/tests -q
	$(BIN)/gdp-lint examples/python

examples:
	cargo run --locked -p gdp --example authorization
	$(BIN)/python examples/python/main.py

wheel:
	$(BIN)/maturin build --release --locked --manifest-path bindings/python/Cargo.toml --out dist

sdist:
	$(BIN)/maturin build --sdist --release --locked --manifest-path bindings/python/Cargo.toml --out dist

package-check: sdist
	cargo package --locked --allow-dirty -p gdp
	$(BIN)/python scripts/check_artifacts.py

audit:
	cargo audit --deny warnings
