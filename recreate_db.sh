export PGPASSWORD=postgres
psql --host 127.0.0.1 -p 5432 -U postgres -d postgres -c "drop database postgres"
psql --host 127.0.0.1 -p 5432 -U postgres -d postgres -c "create database postgres"
