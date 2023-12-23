#!/bin/bash

target_directory="."  # Change this to the directory you want to analyze

total_lines=0

count_lines() {
    local file_path="$1"
    local lines=$(wc -l < "$file_path")
    echo "$lines"
}

is_python_file() {
    local file_name="$1"
    [[ "$file_name" == *.py && ! "$file_name" == *.pyc ]]
}

process_directory() {
    local directory_path="$1"

    for file_path in "$directory_path"/*; do
        if [ -d "$file_path" ] && [ "$(basename "$file_path")" != ".venv" ]; then
            process_directory "$file_path"
        elif [ -f "$file_path" ] && is_python_file "$(basename "$file_path")"; then
            lines=$(count_lines "$file_path")
            total_lines=$((total_lines + lines))
        fi
    done
}

process_directory "$target_directory"

echo "Total lines of code: $total_lines"
