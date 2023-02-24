import datetime as dt
import dropbox
import dropbox.exceptions
import KFS.config, KFS.dropbox, KFS.log
import logging
import time


@KFS.log.timeit
def main(logger: logging.Logger) -> None:
    backup_filenames: list[str]                     #backup filenames
    BACKUPS_PATH="/Apps/Logbook.aero/"              #path to backup files, can't delete folder afterwards because link to Logbook.aero gets destroyed
    dbx: dropbox.Dropbox                            #Dropbox instance
    DEST_PATH="/Dokumente/Luftfahrt/Logbook/"       #destination path for backup files
    DROPBOX_API_TOKEN: str|None                     #Dropbox API access token
    DT_exec_next=dt.datetime.now(dt.timezone.utc)   #next execution
    REFRESH_RATE=1/100                              #work with 10mHz (every 100s)


    DROPBOX_API_TOKEN=KFS.config.load_config("dropbox_API.token")
    if DROPBOX_API_TOKEN==None: #if loading token not possible: exit
        return
    dbx=dropbox.Dropbox(DROPBOX_API_TOKEN)  #create Dropbox instance
    

    while True:
        while dt.datetime.now(dt.timezone.utc)<=DT_exec_next:
            time.sleep(1)
        DT_exec_next=dt.datetime.now(dt.timezone.utc)+dt.timedelta(seconds=DT_exec_next.timestamp()%(1/REFRESH_RATE)+1/REFRESH_RATE)


        try:
            backup_filenames=KFS.dropbox.list_files(dbx, BACKUPS_PATH)  #download content list of backup folder
        except dropbox.exceptions.ApiError:                 #if folder does not exist: do nothing
            logger.warning(f"\"Dropbox{BACKUPS_PATH}\" does not exist. Not doing anything...")
            continue

        if len(backup_filenames)==0: #if backups folder is empty: not doing anything
            logger.info(f"\"Dropbox{BACKUPS_PATH}\" is empty. Not doing anything...")
            continue
        logger.info(f"\"Dropbox{BACKUPS_PATH}\" has contents. Preparing movement.")

        logger.info(f"Deleting existing backup file from today in \"Dropbox{DEST_PATH}\"...") #make room for new backup file first, move can't overwrite
        try:
            dbx.files_delete_v2(f"{DEST_PATH}{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')} Logbook.csv")
        except dropbox.exceptions.ApiError: #TODO What if file exists and deleting failed because of permission error or something?
            logger.warning(f"Backup file from today does not exist yet in \"Dropbox{DEST_PATH}\".")
        else:
            logger.info(f"\rDeleted existing backup file from today in \"Dropbox{DEST_PATH}\".")


        logger.info(f"Moving latest backup file \"{backup_filenames[-1]}\" from \"Dropbox{BACKUPS_PATH}\" to \"Dropbox{DEST_PATH}\"...")
        try:
            dbx.files_move_v2(f"{BACKUPS_PATH}{backup_filenames[-1]}", f"{DEST_PATH}{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')} Logbook.csv")
        except dropbox.exceptions.ApiError:
            logger.error(f"Moving latest backup file \"{backup_filenames[-1]}\" from \"Dropbox{BACKUPS_PATH}\" to \"Dropbox{DEST_PATH}\" failed. Not doing anything...")
            continue
        logger.info(f"\rMoved latest backup file \"{backup_filenames[-1]}\" from \"Dropbox{BACKUPS_PATH}\" to \"Dropbox{DEST_PATH}\".")