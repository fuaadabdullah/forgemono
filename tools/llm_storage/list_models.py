"""
List model artifacts in a GCS bucket under a given prefix and optionally generate signed URLs.

Usage:
  python tools/llm_storage/list_models.py --bucket goblin-assistant-llm --prefix models/7b --signed-url --expiration 3600

"""
from __future__ import annotations

import argparse
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


def list_models(bucket_name: str, prefix: str):
    storage = get_storage()
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = client.list_blobs(bucket_name, prefix=prefix)
    for b in blobs:
        print(b.name)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="List models in a GCS bucket")
    parser.add_argument('--bucket', required=True)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--signed-url', action='store_true')
    parser.add_argument('--expiration', type=int, default=3600)
    args = parser.parse_args(argv)

    storage = get_storage()
    client = storage.Client()
    blobs = client.list_blobs(args.bucket, prefix=args.prefix)
    for b in blobs:
        print(f"gs://{args.bucket}/{b.name}")
        if args.signed_url:
            url = b.generate_signed_url(expiration=args.expiration)
            print(f"  signed: {url}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
