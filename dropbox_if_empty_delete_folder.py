import dropbox
from dropbox_list_files import dropbox_list_files
from KFS import KFSlog


def dropbox_if_empty_delete_folder(dbx, path: str) -> None:
    try:
        backups=dropbox_list_files(dbx, path)
    except dropbox.exceptions.ApiError: #if folder does not exist: do nothing
        KFSlog.write(f"\"{path}\" does not exist. Not doing anything...")
        raise

    if 0<len(backups):  #if backups folder still has contents now: do nothing
        KFSlog.write(f"\"{path}\" is not empty. Not doing anything...")
        raise dropbox.exceptions.ApiError()
    
    KFSlog.write(f"\"{path}\" is empty. Deleting folder...") #if backups path is empty now: delete
    try:
        dbx.files_delete_v2(path[:-1])  #remove trailing slash from path otherwise won't work
    except dropbox.exceptions.ApiError:
        KFSlog.write(f"Deleting folder \"{path}\" failed. Not doing anything...")
        raise
    KFSlog.write(f"\r\"{path}\" is empty. Deleted folder.")

    return