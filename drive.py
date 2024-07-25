import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from tabulate import tabulate

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

def get_gdrive_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    # return Google Drive API service
    return build('drive', 'v3', credentials=creds)

def list_files(items):
    """given items returned by Google Drive API, prints them in a tabular way"""
    if not items:
        # empty drive
        print('No files found.')
    else:
        rows = []
        for item in items:
            # get the File ID
            id = item["id"]
            # get the name of file
            name = item["name"]
            try:
                # parent directory ID
                parents = item["parents"]
            except:
                # has no parrents
                parents = "N/A"
            try:
                # get the size in nice bytes format (KB, MB, etc.)
                size = get_size_format(int(item["size"]))
            except:
                # not a file, may be a folder
                size = "N/A"
            # get the Google Drive type of file
            mime_type = item["mimeType"]
            # get last modified date time
            modified_time = item["modifiedTime"]
            # append everything to the list
            rows.append((id, name, parents, size, mime_type, modified_time))
        print("Files:")
        # convert to a human readable table
        table = tabulate(rows, headers=["ID", "Name", "Parents", "Size", "Type", "Modified Time"])
        # print the table
        print(table)

service = get_gdrive_service()

def get_all_folders_in_drive():
    """
    Return a dictionary of all the folder IDs in a drive mapped to their parent folder IDs (or to the
    drive itself if a top-level folder). That is, flatten the entire folder structure.
    """
    folders_in_drive_dict = {}
    page_token = None
    max_allowed_page_size = 1000
    just_folders = "trashed = false and mimeType = 'application/vnd.google-apps.folder'"
    while True:
        results = drive_api_ref.files().list(
            pageSize=max_allowed_page_size,
            fields="nextPageToken, files(id, name, mimeType, parents)",
            includeItemsFromAllDrives=True, supportsAllDrives=True,
            corpora='drive',
            driveId=DRIVE_ID,
            pageToken=page_token,
            q=just_folders).execute()
        folders = results.get('files', [])
        page_token = results.get('nextPageToken', None)
        for folder in folders:
            folders_in_drive_dict[folder['id']] = folder['parents'][0]
        if page_token is None:
            break
    return folders_in_drive_dict


def get_subfolders_of_folder(folder_to_search, all_folders):
    """
    Yield subfolders of the folder-to-search, and then subsubfolders etc. Must be called by an iterator.
    :param all_folders: The dictionary returned by :meth:`get_all_folders_in-drive`.
    """
    temp_list = [k for k, v in all_folders.items() if v == folder_to_search]  # Get all subfolders
    for sub_folder in temp_list:  # For each subfolder...
        yield sub_folder  # Return it
        yield from get_subfolders_of_folder(sub_folder, all_folders)  # Get subsubfolders etc


def get_relevant_files(self, relevant_folders):
    """
    Get files under the folder-to-search and all its subfolders.
    """
    relevant_files = {}
    chunked_relevant_folders_list = [relevant_folders[i:i + MAX_PARENTS] for i in
                                     range(0, len(relevant_folders), MAX_PARENTS)]
    for folder_list in chunked_relevant_folders_list:
        query_term = ' in parents or '.join('"{0}"'.format(f) for f in folder_list) + ' in parents'
        relevant_files.update(get_all_files_in_folders(query_term))
    return relevant_files


def get_all_files_in_folders(self, parent_folders):
    """
    Return a dictionary of file IDs mapped to file names for the specified parent folders.
    """
    files_under_folder_dict = {}
    page_token = None
    max_allowed_page_size = 1000
    just_files = f"mimeType != 'application/vnd.google-apps.folder' and trashed = false and ({parent_folders})"
    while True:
        results = drive_api_ref.files().list(
            pageSize=max_allowed_page_size,
            fields="nextPageToken, files(id, name, mimeType, parents)",
            includeItemsFromAllDrives=True, supportsAllDrives=True,
            corpora='drive',
            driveId=DRIVE_ID,
            pageToken=page_token,
            q=just_files).execute()
        files = results.get('files', [])
        page_token = results.get('nextPageToken', None)
        for file in files:
            files_under_folder_dict[file['id']] = file['name']
        if page_token is None:
            break
    return files_under_folder_dict


get_all_folders_in_drive()
