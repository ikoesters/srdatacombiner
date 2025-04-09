# %%
from pathlib import Path
import shutil


def move_files_to_folders(foldername: str | Path, file_glob: str) -> None:
    """
    Organize files in a folder by moving them into numbered subfolders.

    This function iterates over all files in the specified folder that match
    the given glob pattern and moves each file into a newly created subfolder.
    The subfolders are named sequentially as "01", "02", "03", etc.

    Args:
        foldername (str | Path): The path to the folder containing the files to organize.
        file_glob (str): A glob pattern to match the files to be moved (e.g., "*.txt").

    Returns:
        None: This function does not return a value. It performs file operations in place.

    Raises:
        FileNotFoundError: If the specified folder does not exist.
        PermissionError: If the program lacks permissions to create subfolders or move files.
        OSError: For other issues related to file or folder operations.

    Example:
        Suppose you have the following files in the folder "data":
            data/file1.txt
            data/file2.txt
            data/file3.txt

        Calling `move_files_to_folders("data", "*.txt")` will organize them into:
            data/01/file1.txt
            data/02/file2.txt
            data/03/file3.txt
    """
    """Iterate over all files in a folder and move them to subfolders."""
    foldername = Path(foldername)

    txt_files = sorted(foldername.glob(file_glob))
    for i, file in enumerate(txt_files, start=1):
        new_folder = foldername / f"{i:02d}"  # Create folder paths as "01", "02", etc.
        new_folder.mkdir(exist_ok=True)

        shutil.move(str(file), str(new_folder / file.name))


# %%
