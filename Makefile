test:
	cd src && \
	pip3 install -r requirements.txt && \
	pip3 install -r requirements-dev.txt && \
	pip3 install -r requirements-ci.txt && \
	python3 -m pytest

lint:
	cd src && \
	pip3 install -r requirements-ci.txt && \
	pip3 install -r requirements.txt && \
	python3 -m pylint --fail-under=9.5 $$(find . -name "*.py" -not -name "test_*")

lint-docstrings:
	cd src && \
	pip3 install -r requirements-ci.txt && \
	darglint_results=$$(find . -name "*.py" -not -name "test_*" -exec darglint {} \; 2>&1) && \
	pydocstyle_results=$$(find . -name "*.py" -not -name "test_*" -exec pydocstyle {} \; 2>&1) && \
	if [ -z "$$darglint_results" ] && [ -z "$$pydocstyle_results" ]; then \
		echo "All docstrings are valid"; \
	else \
		echo "Invalid docstrings found:"; \
		echo "$$darglint_results"; \
		echo "$$pydocstyle_results"; \
		exit 1; \
	fi