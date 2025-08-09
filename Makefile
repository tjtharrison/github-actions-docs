test:
	cd src && \
	python3 -m pytest

lint:
	cd src && \
	python3 -m pylint --fail-under=9.5 $$(find . -name "*.py" -not -name "test_*")