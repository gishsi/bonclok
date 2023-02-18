import os
import shutil

# Copy the file from the specified source path to destination path, the return Boolean value is indicating if the operation succeeded.
def copy_file(sourcePath: str, destinationPath: str) -> bool:
    try:
        shutil.copy(sourcePath, destinationPath)
        return True
    except:
        return False

# Copy the file/directory tree from the specified source path to destination path, the return Boolean value is indicating if the operation succeeded.
def copy_file_tree(sourcePath: str, destinationPath: str) -> bool:
    try:
        shutil.copytree(sourcePath, destinationPath)
        return True
    except:
        return False

# Remove the file at the specified target path, the return Boolean value is indicating if the operation succeeded.
def remove_file_tree(targetPath: str) -> bool:
    try:
        shutil.rmtree(targetPath)
        return True
    except:
        return False

# Create a new directory at the specified target path, the return Boolean value is indicating if the operation succeeded.
def create_directory(targetPath: str) -> bool:
    try:
        os.mkdir(targetPath)
        return True
    except:
        return False

__all__ = [ 'copy_file', 'copy_file_tree', 'remove_file_tree', 'create_directory' ] 