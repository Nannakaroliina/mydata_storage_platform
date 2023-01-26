#!/bin/bash -e
set +x

echo "Setting up the dev env for project"

if [ ! -d "venv" ]; then
  echo "Creating the env... "
  python3 -m venv venv
fi

if [ -d "venv" ]; then
  echo "Activating the venv..."
  source venv/bin/activate

  if [ "$(pip list | grep -F pip-tools)" ]; then
    echo "Pip-tools installed!"
  else
    echo "Install pip-tools for requirements management..."
    pip install pip-tools
  fi

  echo "Install pip dependencies..."
  pip-sync
fi



