import os

def get_files(path_to_dir):
    assert isinstance(path_to_dir, str), "Check if the path is a string."
    abs_path = os.path.abspath(path_to_dir)
    files = os.listdir(abs_path)
    file_list = []
    for file in files:
        file_path = os.path.join(abs_path, file)
        if file.endswith(".root") and os.path.isfile(file_path):
            file_list.append("file:"+file_path)
    return file_list