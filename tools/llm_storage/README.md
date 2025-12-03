# LLM Storage Tools

This folder contains tools to upload and manage LLM artifacts (weights, tokenizer files, configs, and license files) in Google Cloud Storage (GCS) and Google Drive.

Scripts:

- `upload_model.py` - Upload a local file or directory of model files to a GCS bucket. Supports resumable uploads and optional signed URL generation.
- `colab_download_test.py` - Colab-friendly script to download files using signed URLs or service account authentication (GCS).
- `list_models.py` - List models (objects) under a bucket prefix and optionally generate signed URLs (GCS).
- `upload_model_gdrive.py` - Upload files to Google Drive folders; supports public sharing (`--share public`).
- `colab_download_gdrive.py` - Colab-friendly download script for Google Drive folders or Google Drive share links.
- `--licenses` optional path to a license folder to be uploaded under `<dest-folder>/licenses` (for both GCS and Drive uploaders).

Requirements:

- `pip install google-cloud-storage requests`

Example:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/colab-reader-key.json
python tools/llm_storage/upload_model.py --bucket goblin-assistant-llm --src ./models/7b --dest models/7b --licenses ./licenses --signed-url
```

Note: Do not commit credentials to the repo.
