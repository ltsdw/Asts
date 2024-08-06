#! /bin/sh

VENV_DIR="env/asts-env"
ROOT_DIR="$PWD"

create_python_venv()
{
    # Create the directory "env" if it doesn't exists and
    # create a new python virtual environment
    ! [ -d "env" ] && mkdir env && cd env && python3 -m venv asts-env && cd "$ROOT_DIR"
}

venv_activate()
{
    ! [ -f "$VENV_DIR/bin/activate" ] && create_python_venv

    . "$VENV_DIR/bin/activate" > /dev/null 2>&1
}

install_dependencies()
{
    venv_activate
    pip3 install -r requirements.txt
    deactivate
}

install_dependencies
