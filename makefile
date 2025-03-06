# install dependencies
# this project uses uv to manage dependencies
deps:
	uv sync
	uv add . --dev
	uv pip install -e .

# serve the api (requires redis to be running)
dev: 
	PYGEOAPI_CONFIG=local.config.yml PYGEOAPI_OPENAPI=local.openapi.yml pygeoapi serve --starlette

# run pyright to type check the codebase
types:
	uv tool run pyright

test:
	pytest -xn auto
