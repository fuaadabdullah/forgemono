#!/usr/bin/env python3
"""
Small CLI tool to upload model files and license files to a GCS bucket.

Usage (env var + CLI):
  export GOOGLE_APPLICATION_CREDENTIALS=path/to/sa-key.json
  python tools/llm_storage/upload_model.py --bucket my-bucket --src ./models/7b --dest models/7b --licenses ./licenses

Features:
- Resumable uploads for large files
- Optionally create signed URLs (for short-lived sharing)
- Writes licenses under <dest>/licenses/
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

_storage = None


def get_storage():
    global _storage
    if _storage is None:
        try:
            from google.cloud import storage as _s
        except Exception as e:
            raise RuntimeError("google-cloud-storage is required. Install via: pip install google-cloud-storage") from e
        _storage = _s
    return _storage


def upload_file(bucket, source_path: Path, dest_path: str, chunk_size: int = 256 * 1024) -> None:
    blob = bucket.blob(dest_path)
    # Use resumable upload for large files
    blob.chunk_size = chunk_size
    print(f"Uploading {source_path} -> gs://{bucket.name}/{dest_path}")
    blob.upload_from_filename(str(source_path), timeout=60 * 10)


def create_signed_url(bucket, dest_path: str, expiration: int = 60 * 60) -> str:
    blob = bucket.blob(dest_path)
    url = blob.generate_signed_url(expiration=expiration)
    return url


def upload_dir(bucket, src_dir: Path, dest_prefix: str, include_hidden: bool = False) -> None:
    for root, _, files in os.walk(src_dir):
        for f in files:
            if not include_hidden and f.startswith('.'):
                continue
            src_file = Path(root) / f
            rel_path = src_file.relative_to(src_dir)
            dest = f"{dest_prefix}/{rel_path.as_posix()}"
            upload_file(bucket, src_file, dest)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Upload model files and license files to Google Cloud Storage")
    parser.add_argument("--bucket", required=True, help="GCS bucket name")
    parser.add_argument("--src", type=Path, required=True, help="Local source path to upload (file or directory)")
    parser.add_argument("--dest", required=True, help="Destination prefix in the bucket (e.g. 'models/7b')")
    parser.add_argument("--licenses", type=Path, help="Optional path to license files (folder) to upload under <dest>/licenses")
    parser.add_argument("--signed-url", action="store_true", help="Print signed URL(s) for uploaded files")
    parser.add_argument("--expiration", type=int, default=60 * 60, help="Signed URL expiration seconds (default 1h)")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files in uploads")

    args = parser.parse_args(argv)

    storage = get_storage()
    client = storage.Client()
    bucket = client.bucket(args.bucket)
    if not bucket.exists():
        print(f"Bucket gs://{args.bucket} does not exist or you do not have permission.")
        return 2

    print(f"Connected to bucket: gs://{args.bucket}")
    if args.src.is_dir():
        upload_dir(bucket, args.src, args.dest, include_hidden=args.include_hidden)
    elif args.src.is_file():
        upload_file(bucket, args.src, f"{args.dest}/{args.src.name}")
    else:
        print(f"Source {args.src} does not exist")
        return 1

    if args.licenses:
        if not args.licenses.exists():
            print(f"Licenses path {args.licenses} does not exist")
        else:
            licenses_dest = f"{args.dest}/licenses"
            upload_dir(bucket, args.licenses, licenses_dest, include_hidden=args.include_hidden)

    if args.signed_url:
        print("Creating signed URLs for uploaded files under prefix: {args.dest}")
        # List objects under dest and print a signed URL for each
        blobs = client.list_blobs(args.bucket, prefix=args.dest)
        for b in blobs:
            url = create_signed_url(bucket, b.name, expiration=args.expiration)
            print(f"gs://{args.bucket}/{b.name} -> {url}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
