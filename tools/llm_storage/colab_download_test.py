"""
Simple download example for Colab environment.

Usage:
- With signed URL(s): Set environment variable `SIGNED_URLS` containing a comma-separated list of URLs.
- With service account: Set `GOOGLE_APPLICATION_CREDENTIALS` to your key file and provide `BUCKET` and `OBJECT_PATH` environment variables.

This script will download the model file to `/content/model_test/` in Colab.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional


def download_signed_urls(urls: List[str], output_dir: Path) -> None:
    import requests

    output_dir.mkdir(parents=True, exist_ok=True)
    for idx, url in enumerate(urls, 1):
        filename = url.split('?')[0].split('/')[-1] or f"download_{idx}"
        dst = output_dir / filename
        print(f"Downloading signed URL: {url} -> {dst}")
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(dst, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def download_from_gcs(bucket_name: str, object_path: str, output_dir: Path) -> None:
    from google.cloud import storage

    output_dir.mkdir(parents=True, exist_ok=True)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_path)
    dst = output_dir / Path(object_path).name
    print(f"Downloading gs://{bucket_name}/{object_path} -> {dst}")
    blob.download_to_filename(str(dst))


def main():
    out_dir = Path(os.environ.get('OUT_DIR', '/content/model_test'))

    signed_urls = os.environ.get('SIGNED_URLS')
    if signed_urls:
        download_signed_urls([u.strip() for u in signed_urls.split(',') if u.strip()], out_dir)
        return 0

    bucket = os.environ.get('BUCKET')
    object_path = os.environ.get('OBJECT_PATH')
    if bucket and object_path:
        download_from_gcs(bucket, object_path, out_dir)
        return 0

    print("Provide either SIGNED_URLS or (BUCKET + OBJECT_PATH) environment variables.")
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
