import dropbox


def dropbox_list_files(dbx, path: str) -> list: #list[str] doesnt work on server
    file_names=[]   #file names to return


    result=dbx.files_list_folder(path)  #read first batch of file names
    file_names+=[entry.name for entry in result.entries if isinstance(entry, dropbox.files.FileMetadata)==True] #append file names, exclude all non-files

    while result.has_more==True:    #as long as more file names still unread: continue
        result=dbx.files_list_folder_continue(result.cursor)
        file_names+=[entry.name for entry in result.entries if isinstance(entry, dropbox.files.FileMetadata)==True] #append file names, exclude all non-files

    file_names.sort()   #sort file names before returning

    return file_names