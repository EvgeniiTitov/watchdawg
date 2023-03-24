install-req-dev:
	pip install --upgrade pip
	pip install requirements/requirements-dev.txt


install-req-prod:
	pip install --upgrade pip
	pip install requirements/requirements-prod.txt


set-up-precommit:
	pre-commit install


run-precommit:
	pre-commit run --all-files -v