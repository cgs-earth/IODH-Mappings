# install dependencies
# this project uses uv to manage dependencies
deps:
	uv sync
	uv add . --dev
	uv pip install -e .

# serve the api (requires redis to be running)
dev: 
	pygeoapi openapi generate local.config.yml --output-file local.openapi.yml
	PYGEOAPI_CONFIG=local.config.yml PYGEOAPI_OPENAPI=local.openapi.yml pygeoapi serve --starlette

devNoOTEL:
	pygeoapi openapi generate local.config.yml --output-file local.openapi.yml
	OTEL_SDK_DISABLED=true PYGEOAPI_CONFIG=local.config.yml PYGEOAPI_OPENAPI=local.openapi.yml pygeoapi serve --starlette

test:
	 pytest -n auto -x --maxfail=1 -vv
