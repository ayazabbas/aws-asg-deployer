deps:
	poetry install

lint:
	poetry run black asgd/
	poetry run isort asgd/
	poetry run flake8 --ignore E501 asgd/
