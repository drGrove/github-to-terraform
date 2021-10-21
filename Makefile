.PHONY: test
test:
	python3 -m unittest -v

.PHONY: setup
setup:
	pipenv install

.PHONY: shell
shell:
	pipenv shell
