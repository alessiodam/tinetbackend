#!/bin/bash

## check for .env and load it
if [ ! -f .env ]; then
  export $(cat .env | xargs)
fi

## Function to check if docker-compose.yml has been modified
docker_compose_modified() {
    local old_mtime=$(stat -c %Y docker-compose.yml)
    git pull
    git_fetch_result=$?
    local new_mtime=$(stat -c %Y docker-compose.yml)
    if [ $new_mtime -gt $old_mtime ]; then
        return 0
    else
        return 1
    fi
}

## Fetch and check if docker-compose.yml has been modified
echo "pulling"
if docker_compose_modified; then
    docker_actions=true
else
    docker_actions=false
fi

if [ ! -d ".venv" ]; then
    echo "Creating venv"
    python3 -m venv .venv
fi

echo "Activating virtual environment"
source .venv/bin/activate

echo "Installing dependencies"
pip install -r requirements.txt -U

## Django things
echo "Checking for Django migrations"
python manage.py showmigrations --plan > /dev/null 2>&1
if [ $? -eq 1 ]; then
    echo "There are Django migrations available. Exiting."
    exit 1
else
    echo "There are no Django migrations available. Proceeding with the update."
fi

## Copy over all the static files
echo "Copying over files for nginx to static dir."
python manage.py collectstatic --noinput

## Docker related actions
if [ "$docker_actions" = true ]; then
    echo "Updating docker stack."
    echo "Shutting down docker stack."
    sudo docker-compose down
    echo "Starting docker stack."
    sudo docker-compose up -d

    echo "Copying systemd service file"
    sudo cp tinetbackend.service /etc/systemd/system/

    echo "Reloading systemd daemon"
    sudo systemctl daemon-reload
fi

echo "Update completed"

## Run stuff
echo "Starting server"
gunicorn -c gunicorn.conf.py tinetbackend.wsgi:application
