#!/bin/bash

# Define the results directory
RESULTS_DIR="workspace/results"

# Loop through each folder in the results directory
for folder in "$RESULTS_DIR"/*; do
	# Check if the folder is a directory
	if [ -d "$folder" ]; then
		# Find all subdirectories and files within the folder and delete them
		find "$folder" -mindepth 1 -delete
		# After deleting the contents, try to remove the folder itself
		# rmdir will only succeed if the folder is empty
		rmdir "$folder"
	fi
done