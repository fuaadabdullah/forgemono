"""
Colab-friendly script to download files from a Google Drive folder using either
service account (via GOOGLE_APPLICATION_CREDENTIALS) or standard OAuth (user consent).

Usage (service account):
  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/colab-reader-key.json
  python tools/llm_storage/colab_download_gdrive.py --folder-id <DRIVE_FOLDER_ID>

Usage (signed share links):
  export SIGNED_LINKS=<comma-separated-links>
  python tools/llm_storage/colab_download_gdrive.py --signed-links
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List


def download_signed_links(links: List[str], output_dir: Path):
    import requests
    output_dir.mkdir(parents=True, exist_ok=True)
    for link in links:
        name = link.split('?')[0].split('/')[-1]
        dst = output_dir / name
        print(f"Downloading {link} -> {dst}")
        r = requests.get(link, stream=True)
        r.raise_for_status()
        with open(dst, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def download_from_drive_folder(folder_id: str, output_dir: Path):
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
    except Exception as e:
        raise RuntimeError('googleapiclient/google-auth required; pip install google-api-python-client google-auth') from e
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path:
        raise RuntimeError('Set GOOGLE_APPLICATION_CREDENTIALS for service account JSON path')
    scopes = ['https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=scopes)
    service = build('drive', 'v3', credentials=creds)
    page_token = None
    output_dir.mkdir(parents=True, exist_ok=True)
    import io
    from googleapiclient.http import MediaIoBaseDownload
    while True:
        param = {'q': f"'{folder_id}' in parents", 'fields': 'nextPageToken, files(id, name)', 'pageSize': 100}
        if page_token:
            param['pageToken'] = page_token
        res = service.files().list(**param).execute()
        files = res.get('files', [])
        for f in files:
            fname = f['name']
            fid = f['id']
            print(f"Downloading: {fname}")
            request = service.files().get_media(fileId=fid)
            fh = open(output_dir / fname, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        page_token = res.get('nextPageToken', None)
        if not page_token:
            break


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description='Download files from Google Drive folder (service account or signed links)')
    parser.add_argument('--folder-id', help='Drive folder id')
    parser.add_argument('--signed-links', action='store_true', help='Use SIGNED_LINKS env var with comma list of URLs')
    parser.add_argument('--out-dir', default='/content/model_test')
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    if args.signed_links:
        links = os.environ.get('SIGNED_LINKS', '')
        if not links:
            print('Set SIGNED_LINKS env var')
            return 1
        download_signed_links([x.strip() for x in links.split(',') if x.strip()], out_dir)
        return 0
    if args.folder_id:
        download_from_drive_folder(args.folder_id, out_dir)
        return 0
    print('Provide either --signed-links (and SIGNED_LINKS env var) or --folder-id')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
