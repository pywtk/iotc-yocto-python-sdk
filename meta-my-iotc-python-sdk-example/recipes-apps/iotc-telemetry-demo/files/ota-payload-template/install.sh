#!/bin/bash

application_payload_dir="./application/"
local_data_payload_dir="./local_data/"

# Source directory to be backed up
application_installed_dir="/usr/bin/local/iotc/"
local_data_installed_dir="/usr/local/iotc/"
application_backup_dir="${application_installed_dir::-1}.backup/"
local_data_backup_dir="${local_data_installed_dir::-1}.backup/"

tuples=("$application_installed_dir $application_backup_dir" "$local_data_installed_dir $local_data_backup_dir")
for tuple in "${tuples[@]}"; do
    eval "tuple=($tuple)"
    installed_dir="${tuple[0]}"
    backup_dir="${tuple[1]}"

        if [ -d "$backup_dir" ]; then
            echo "Removing existing backup... at $backup_dir"
            rm -r "$backup_dir"
        fi

        echo "Creating backup directories at $backup_dir"
        mkdir -p "$backup_dir"

        echo "backing up  $installed_dir to $backup_dir"
        cp -r "$installed_dir" "$backup_dir"
done

# # Initialize an empty array to store the file names
# file_array=()

# # Check if the folder exists
# if [ -d "$folder" ]; then
#     # Use a for loop to iterate over the files in the folder
#     for file in "$folder"/*; do
#         # Add the file to the array
#         file_array+=("$file")
#     done
# else
#     echo "Folder not found."
# fi

# # Display the list of files in the array
# for file in "${file_array[@]}"; do
#     echo "$file"
# done


# # Check if the source file exists
# if [ -e "$source_file" ]; then
#     # Replace the destination file with the source file
#     cp -f "$source_file" "$destination_file"
#     echo "File replaced successfully."
# else
#     echo "Source file does not exist, no replacement performed."
# fi

