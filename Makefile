test:
	cd src && \
	pip3 install -r src/requirements.txt && \
	pip3 install -r src/requirements-dev.txt && \
	pip3 install -r src/requirements-ci.txt && \
	python3 -m pytest

lint:
	cd src && \
	python3 -m pylint --fail-under=9.5 $$(find . -name "*.py" -not -name "test_*")