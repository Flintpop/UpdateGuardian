# -----------------------------------------------------------
# add_paths.py
# Author: darwh
# Date: 09/05/2023
# Description: 
# -----------------------------------------------------------
import os
import sys

root_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(root_dir, "..", "..")  # Go to the root directory (UpdateGuardian)

# Add the root directory (src) to sys.path
sys.path.append(root_dir)

# Add all subdirectories in the root directory (src) to sys.path
for subdir in os.listdir(root_dir):
    subdir_path = os.path.join(root_dir, subdir)
    if os.path.isdir(subdir_path):
        sys.path.append(subdir_path)
