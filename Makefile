PYTHON ?= python

.PHONY: all run test lint figures tables patches clean

all: run figures tables

# Full reproduction pipeline
run:
	./run_all.sh

# Unit/regression tests live under hypatiax/experiments/tests
test:
	$(PYTHON) -m pytest hypatiax/experiments/tests/

# Lint the package and scripts
lint:
	$(PYTHON) -m flake8 hypatiax/ scripts/

# Regenerate paper figures
figures:
	$(PYTHON) scripts/generate_figures.py

# Regenerate paper tables
tables:
	$(PYTHON) scripts/generate_tables.py

# Run the analysis patch scripts (comparison tables + input validation)
patches:
	$(PYTHON) scripts/patches/generate_exp2_pca_comparison_table.py
	$(PYTHON) scripts/patches/generate_nguyen12_symequiv_table.py
	$(PYTHON) scripts/patches/validate_analysis_input.py

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} +
	find . -name '*.pyc' -delete
