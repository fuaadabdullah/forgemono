#!/usr/bin/env python3
"""
Upload files to a Google Drive folder using the Google Drive API (v3).

Usage:
  export GOOGLE_APPLICATION_CREDENTIALS=path/to/sa-key.json
  python tools/llm_storage/upload_model_gdrive.py --folder-id <DRIVE_FOLDER_ID> --src ./models/7b --share public

Notes:
- The service account must be granted access to the folder (either by sharing the folder with the service account email or by using an OAuth flow.)
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Optional

_drive = None


def get_drive_service():
    global _drive
    if _drive is None:
        try:
            from googleapiclient.discovery import build
            from google.oauth2 import service_account
        except Exception as e:
            raise RuntimeError("googleapiclient/google-auth are required. Install via: pip install google-api-python-client google-auth") from e

        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            raise RuntimeError('Set GOOGLE_APPLICATION_CREDENTIALS to your service account json')
        scopes = ['https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=scopes)
        _drive = build('drive', 'v3', credentials=creds)
    return _drive


def upload_file_to_folder(service, file_path: Path, folder_id: str, chunk_size: int = 256 * 1024):
    from googleapiclient.http import MediaFileUpload

    file_metadata = {
        'name': file_path.name,
        'parents': [folder_id],
    }
    media = MediaFileUpload(str(file_path), resumable=True, chunksize=chunk_size)
    request = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink')
    response = None
    while response is None:
        status, response = request.next_chunk()
    return response


def create_folder_if_not_exists(service, parent_folder_id: Optional[str], folder_name: str) -> str:
    # look for folder by name under parent
    q = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'"
    if parent_folder_id:
        q += f" and '{parent_folder_id}' in parents"
    res = service.files().list(q=q, spaces='drive', fields='files(id, name)')
    files = res.execute().get('files', [])
    if files:
        return files[0]['id']
    body = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_folder_id:
        body['parents'] = [parent_folder_id]
    folder = service.files().create(body=body, fields='id').execute()
    return folder['id']


def walk_and_upload(service, src: Path, folder_id: str, include_hidden: bool = False):
    if src.is_file():
        return [upload_file_to_folder(service, src, folder_id)]
    uploaded = []
    for root, _, files in os.walk(src):
        for f in files:
            if not include_hidden and f.startswith('.'):
                continue
            fp = Path(root) / f
            uploaded.append(upload_file_to_folder(service, fp, folder_id))
    return uploaded


def share_file_public(service, file_id: str):
    body = {'role': 'reader', 'type': 'anyone'}
    perm = service.permissions().create(fileId=file_id, body=body, fields='id').execute()
    return perm


def main(argv=None):
    parser = argparse.ArgumentParser(description='Upload model files to Google Drive folder')
    parser.add_argument('--folder-id', help='Drive folder id to upload into')
    parser.add_argument('--parent-folder-id', help='Optional parent folder id; will create child folder if not exists')
    parser.add_argument('--dest-folder', default='goblin-assistant-models', help='Folder name to create under parent (or root)')
    parser.add_argument('--src', type=Path, required=True)
    parser.add_argument('--include-hidden', action='store_true')
    parser.add_argument('--share', choices=['public', 'private'], default='private', help='Make files public (anyone with link)')
    parser.add_argument('--licenses', type=Path, help='Optional path to license files to upload under <dest-folder>/licenses')

    args = parser.parse_args(argv)
    service = get_drive_service()

    folder_id = args.folder_id
    if not folder_id:
        folder_id = create_folder_if_not_exists(service, args.parent_folder_id, args.dest_folder)
    uploaded = walk_and_upload(service, args.src, folder_id, include_hidden=args.include_hidden)
    if args.licenses:
        if not args.licenses.exists():
            print(f"Licenses path {args.licenses} does not exist")
        else:
            licenses_folder_id = create_folder_if_not_exists(service, folder_id, 'licenses')
            walk_and_upload(service, args.licenses, licenses_folder_id, include_hidden=args.include_hidden)
    if args.share == 'public':
        for u in uploaded:
            file_id = u.get('id')
            try:
                share_file_public(service, file_id)
            except Exception:
                pass
    for u in uploaded:
        print('Uploaded:', u)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
