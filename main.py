import datetime as dt
import dropbox
import dropbox.exceptions
import time
from KFS import KFSlog
from dropbox_if_empty_delete_folder import dropbox_if_empty_delete_folder
from dropbox_list_files import dropbox_list_files


@KFSlog.timeit
def main():
    backups=None                                    #backup file names
    BACKUPS_PATH="/Apps/Logbook.aero/"              #path to backup files
    BACKUPS_PATH_PARENT="/Apps/"
    dbx=None                                        #Dropbox instance
    DEST_PATH="/Dokumente/Luftfahrt/Logbook/"       #destination path for backup files
    DROPBOX_API_TOKEN=""                            #Dropbox API access token
    DT_exec_next=dt.datetime.now(dt.timezone.utc)   #next execution
    REFRESH_RATE=1/100                              #work with 10mHz (every 100s)


    KFSlog.write("Loading dropbox API token...")
    with open("dropbox_API_token.txt", "rt") as dropbox_API_token_file:
        DROPBOX_API_TOKEN=dropbox_API_token_file.read() #read API access token
    KFSlog.write("\rLoaded dropbox API token.")

    dbx=dropbox.Dropbox(DROPBOX_API_TOKEN)  #create Dropbox instance
    

    while True:
        while dt.datetime.now(dt.timezone.utc)<=DT_exec_next:
            time.sleep(1)
        DT_exec_next=dt.datetime.now(dt.timezone.utc)+dt.timedelta(seconds=DT_exec_next.timestamp()%(1/REFRESH_RATE)+1/REFRESH_RATE)


        try:
            backups=dropbox_list_files(dbx, BACKUPS_PATH)   #download content list of backup folder
        except dropbox.exceptions.ApiError:                 #if folder does not exist: do nothing
            KFSlog.write(f"\"Dropbox/{BACKUPS_PATH}\" does not exist. Not doing anything...")
            continue

        if len(backups)==0: #if backups folder is empty: delete
            KFSlog.write(f"\"Dropbox/{BACKUPS_PATH}\" is empty. Deleting folder...")
            try:
                dbx.files_delete_v2(BACKUPS_PATH[:-1])  #remove trailing slash from path otherwise won't work
            except dropbox.exceptions.ApiError:
                KFSlog.write(f"Deleting folder \"Dropbox/{BACKUPS_PATH}\" failed. Not doing anything...")
                continue
            KFSlog.write(f"\r\"Dropbox/{BACKUPS_PATH}\" is empty. Deleted folder.")
            dropbox_if_empty_delete_folder(dbx, BACKUPS_PATH_PARENT)
            continue
        else:
            KFSlog.write(f"\"Dropbox/{BACKUPS_PATH}\" has contents. Preparing movement.")

        KFSlog.write(f"Deleting existing backup file from today in \"Dropbox/{DEST_PATH}\"...") #make room for new backup file first, move can't overwrite
        try:
            dbx.files_delete_v2(f"{DEST_PATH}{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')} Logbook.csv")
        except dropbox.exceptions.ApiError:
            KFSlog.write(f"Backup file from today does not exist yet in \"Dropbox/{DEST_PATH}\".")
        else:
            KFSlog.write(f"\rDeleted existing backup file from today in \"Dropbox/{DEST_PATH}\".")


        KFSlog.write(f"Moving latest backup file \"{backups[-1]}\" from \"Dropbox/{BACKUPS_PATH}\" to \"Dropbox/{DEST_PATH}\"...")
        try:
            dbx.files_move_v2(f"{BACKUPS_PATH}{backups[-1]}", f"{DEST_PATH}{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')} Logbook.csv")
        except dropbox.exceptions.ApiError:
            KFSlog.write(f"Moving latest backup file \"{backups[-1]}\" from \"Dropbox/{BACKUPS_PATH}\" to \"Dropbox/{DEST_PATH}\" failed. Not doing anything...")
            continue
        KFSlog.write(f"\rMoved latest backup file \"{backups[-1]}\" from \"Dropbox/{BACKUPS_PATH}\" to \"Dropbox/{DEST_PATH}\".")


        try:
            dropbox_if_empty_delete_folder(dbx, BACKUPS_PATH)
            dropbox_if_empty_delete_folder(dbx, BACKUPS_PATH_PARENT)
        except dropbox.exceptions.ApiError:
            continue