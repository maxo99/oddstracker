


clear_db:
	docker compose exec -T postgres psql -U postgres -d oddstracker -c "DROP TABLE IF EXISTS betoffer CASCADE; DROP TABLE IF EXISTS event CASCADE;"