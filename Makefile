.PHONY: run embed eval docker docker-run deploy port-forward

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

embed:
	python scripts/precompute.py

eval:
	python evals/run_evals.py

docker:
	docker build -t commerce-agent:latest .

docker-run:
	docker run --rm -p 8000:8000 --env-file .env commerce-agent:latest

deploy:
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/ingress.yaml

port-forward:
	kubectl port-forward service/commerce-agent 8012:80
