.PHONY: build push run stop clean test

IMAGE_NAME = ashfromsky/yaradb
VERSION = latest

build:
	docker build -t $(IMAGE_NAME):$(VERSION) .

build-no-cache:
	docker build --no-cache -t $(IMAGE_NAME):$(VERSION) .

push:
	docker push $(IMAGE_NAME):$(VERSION)

release: build push
	@echo "✅ Released $(IMAGE_NAME):$(VERSION)"

run:
	docker run -d -p 8000:8000 \
		-v $$(pwd)/yaradb_data:/data \
		-e DATA_DIR=/data \
		--name yaradb_server \
		$(IMAGE_NAME):$(VERSION)

stop:
	docker stop yaradb_server || true
	docker rm yaradb_server || true

restart: stop run

logs:
	docker logs -f yaradb_server

clean: stop
	docker rmi $(IMAGE_NAME):$(VERSION) || true
	rm -rf yaradb_data

test:
	docker run --rm $(IMAGE_NAME):$(VERSION) pytest tests/ -v

size:
	docker images $(IMAGE_NAME):$(VERSION) --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

shell:
	docker exec -it yaradb_server /bin/bash

health:
	curl http://localhost:8000/ping