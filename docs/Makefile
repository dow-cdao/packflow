.PHONY: api dev build prod-build prod-serve serve-prebuilt gh-pages-stage gh-pages-push

api:
	@echo "Deleting old auto-generated docs"
	rm -rf ./source/api-reference/auto
	mkdir -p ./source/api-reference/auto
	@echo "Generating API docs"
	sphinx-apidoc -o ./source/api-reference/auto ../src/packflow

dev: api
	rm -rf ./dev-build/*/
	sphinx-autobuild source dev-build/html --watch ../src/packflow/ --watch ../examples/ --watch ../LICENSE --port 8000

build: api
	@echo 'Cleaning old build artifacts...'
	rm -rf build/html
	@echo 'Building documentation'
	sphinx-build source build/html

prod-build: api
	@if [ ! -d ../.git ]; then \
	    echo 'ERROR: .git directory not found. prod-build requires Git history to identify branches/tags.'; \
		echo 'Use "make dev" instead for development, or download source with Git history.'; \
		exit 1; \
	fi
	@echo 'Cleaning old production build artifacts...'
	rm -rf build/html
	@echo 'Building multi-version documentation site from designated branches...'
	sphinx-multiversion source build/html

prod-serve: prod-build
	open http://localhost:8000/
	cd build/html && python -m http.server 8000

serve-prebuilt:
	@echo 'Serving pre-built documentation from build/html...'
	@echo 'Access docs at: http://localhost:8000/'
	cd build/html && python -m http.server 8000

gh-pages-stage: build
	@if [ ! -d build/html ]; then \
		echo 'ERROR: build/html not found. Run a docs build first (e.g. make dev or sphinx-build source build/html).'; \
		exit 1; \
	fi
	@echo 'Staging Documentation for GitHub pages...'
	rm -rf gh-pages-staging
	cp -r build/html gh-pages-staging
	rm -rf gh-pages-staging/.doctrees
	touch gh-pages-staging/.nojekyll
	@echo 'Staged to: docs/gh-pages-staging'
	@echo 'Review built documentation for issues, then run: make gh-pages-push to publish'

gh-pages-push:
	@if [ ! -d gh-pages-staging]; then \
		echo 'ERROR: gh-pages-staging not found. Run make gh-pages-stage first.'; \
		exit 1; \
	fi
	@echo 'Pushing docs/gh-pages-staging/ to gh-pages branch...'
	cd gh-pages-staging && \
	    git init && \
		git config user.name "$$(git -C .. config --local user.name)" && \
		git config user.email "$$(git -C .. config --local user.email)" && \
		git add -A && \
		git commit -m "docs: update GitHub Pages" && \
		git push --force $$(git -C .. remote get-url origin) HEAD:gh-pages
