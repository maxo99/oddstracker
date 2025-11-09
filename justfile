


clear_db:
	docker compose exec -T oddstracker-postgres psql -U postgres -d oddstracker -c "DROP TABLE IF EXISTS eventoffer CASCADE; DROP TABLE IF EXISTS sportevent CASCADE; DROP TABLE IF EXISTS teamdata CASCADE;"