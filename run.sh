#!/bin/bash

# Function to kill both processes
function cleanup() {
    echo "Stopping both processes..."
    kill %1 %2  # Kills the jobs running in background
}

# Trap SIGINT (Ctrl+C) and call cleanup function
trap cleanup SIGINT

# Start both make commands in the background
make run-frontend &
make run-backend &

# Wait for both processes to exit
wait