.PHONY: api dev prod-build prod-serve serve-prebuilt

api:
	@echo "Deleting old auto-generated docs"
	rm -rf ./source/api-reference/auto
	mkdir -p ./source/api-reference/auto
	@echo "Generating API docs"
	sphinx-apidoc -o ./source/api-reference/auto ../src/packflow

dev: api
	rm -rf ./dev-build/*/
	sphinx-autobuild source dev-build/html --watch ../src/packflow/ --watch ../examples/ --watch ../LICENSE --port 8000

prod-build: api
	@if [ ! -d ../.git ]; then \
	    echo 'ERROR: .git directory not found. prod-build requires Git history to identify branches/tags.'; \
		echo 'Use "make dev" instead for development, or download source with Git history.'; \
		exit 1; \
	fi
	@echo 'Cleaning old production build artifacts...'
	rm -rf build/html/*/
	@echo 'Building production site from designated branches...'
	sphinx-multiversion source build/html

prod-serve: prod-build
	open http://localhost:8000/
	cd build/html && python -m http.server 8000

serve-prebuilt:
	@echo 'Serving pre-built documentation from build/html...'
	@echo 'Access docs at: http://localhost:8000/'
	cd build/html && python -m http.server 8000
