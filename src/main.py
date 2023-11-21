# Copyright (c) 2023 구FS, all rights reserved. Subject to the MIT licence in `licence.md`.
import datetime as dt
import dropbox
import dropbox.exceptions
import json
from KFSconfig  import KFSconfig
from KFSdropbox import KFSdropbox
from KFSfstr    import KFSfstr
from KFSlog     import KFSlog
import logging
import os
import time


@KFSlog.timeit
def main(DEBUG: bool, logger: logging.Logger) -> None:
    dbx: dropbox.Dropbox                                        # dropbox instance
    dest_dir_filenames: list[str]                               # filenames in destination directory
    dest_filepath: str                                          # destination filepath
    DEST_PATH="/Documents/Aviation/Logbook/"                    # destination path for backup files
    dropbox_API_cred: dict[str, str]                            # dropbox API access credentials
    DROPBOX_API_CRED_DEFAULT: dict[str, str]={                   # dropbox configuration default content
        "app_key": "",
        "app_secret": "",
        "refresh_token": "",
    }
    exec_next_DT: dt.datetime=dt.datetime.now(dt.timezone.utc)  # next execution
    refresh_rate: float                                         # how often to refresh
    source_dir_filenames: list[str]                             # filenames in source directory
    source_filepath: str                                        # source filepath
    SOURCE_PATH="/Apps/Logbook.aero/"                           # path to backup files, can't delete folder afterwards because link to Logbook.aero gets destroyed


    if logger.level<=logging.DEBUG:                                                                                                                             # if debug mode:
        refresh_rate=1/10                                                                                                                                       # refresh with 100mHz (every 10s)
    else:                                                                                                                                                       # if normal mode:
        refresh_rate=1/100                                                                                                                                      # refresh with 10mHz (every 100s)
    try:
        dropbox_API_cred=json.loads(KFSconfig.load_config("./config/dropbox_API_cred.json", json.dumps(DROPBOX_API_CRED_DEFAULT, indent=4)))                    # load API credentials
    except FileNotFoundError:
        return
    dbx=dropbox.Dropbox(oauth2_refresh_token=dropbox_API_cred["refresh_token"], app_key=dropbox_API_cred["app_key"], app_secret=dropbox_API_cred["app_secret"]) # create Dropbox instance
    

    while True:
        while dt.datetime.now(dt.timezone.utc)<=exec_next_DT:
            time.sleep(1)
        exec_next_DT=dt.datetime.now(dt.timezone.utc)+dt.timedelta(seconds=1/refresh_rate-exec_next_DT.timestamp()%(1/refresh_rate))    # when refresh next time?


        try:
            source_dir_filenames=KFSdropbox.list_files(dbx, SOURCE_PATH)    # download content list of backup source folder
        except dropbox.exceptions.ApiError:                                 # if folder does not exist: do nothing
            logger.error(f"Source directory \"Dropbox{SOURCE_PATH}\" does not exist. Unable to work. Shutdown...")
            break

        if len(source_dir_filenames)==0:    # if backups folder is empty: not doing anything
            logger.info(f"Source directory \"Dropbox{SOURCE_PATH}\" is empty. Waiting {KFSfstr.notation_tech(1/refresh_rate, 2)}s...")
            continue
        logger.info(f"Source directory \"Dropbox{SOURCE_PATH}\" has contents. Preparing movement.")

        source_filepath=f"{SOURCE_PATH}{source_dir_filenames[-1]}"
        logger.debug(f"Source filepath: \"{source_filepath}\"")
        dest_filepath=f"{DEST_PATH}{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')} Logbook.csv"
        logger.debug(f"Destination filepath: \"{dest_filepath}\"")
        
        try:
            dest_dir_filenames=KFSdropbox.list_files(dbx, DEST_PATH)    # download content list of backup destination folder
        except dropbox.exceptions.ApiError:                             # if folder does not exist: do nothing
            logger.warning(f"Destination directory filenames could not be downloaded. Source directory \"Dropbox{DEST_PATH}\" probably does not exist yet.")
            dest_dir_filenames=[]                                       # default empty list
        
        if os.path.basename(dest_filepath) in dest_dir_filenames:                                   # if backup file already exists:
            logger.info(f"Deleting existing backup file from today \"Dropbox{dest_filepath}\"...")  # make room for new backup file first, move can't overwrite
            try:
                dbx.files_delete_v2(dest_filepath)
            except dropbox.exceptions.ApiError:                                                     # if deleting unsuccessful: give up this time
                logger.error(f"Deleting existing backup file from today \"Dropbox{dest_filepath}\" failed. Aborting movement...")
                continue
            else:
                logger.info(f"\rDeleted existing backup file from today \"Dropbox{dest_filepath}\".")


        logger.info(f"Moving latest backup file \"{source_dir_filenames[-1]}\" from source directory \"Dropbox{SOURCE_PATH}\" to destination directory \"Dropbox{DEST_PATH}\"...")
        try:
            dbx.files_move_v2(source_filepath, dest_filepath)
        except dropbox.exceptions.ApiError:
            logger.error(f"Moving latest backup file \"{source_dir_filenames[-1]}\" from source directory \"Dropbox{SOURCE_PATH}\" to destination directory \"Dropbox{DEST_PATH}\" failed.")
            continue
        logger.info(f"\rMoved latest backup file \"{source_dir_filenames[-1]}\" from source directory \"Dropbox{SOURCE_PATH}\" to destination directory \"Dropbox{DEST_PATH}\".")

    return