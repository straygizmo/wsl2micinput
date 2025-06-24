#!/bin/bash

# Wrapper script to run examples with virtual environment activated

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup script..."
    ./setup/install_dependencies.sh
fi

# Activate virtual environment
source venv/bin/activate

# Run the example script with all passed arguments
python "$@"