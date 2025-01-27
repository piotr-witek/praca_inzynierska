docker-compose up -d <- to start DB
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py runserver
docker compose down <- to close DB


coverage run manage.py test
coverage report
coverage html