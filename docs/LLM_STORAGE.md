# Storing LLM Models in Google Cloud Storage (GCS)

This doc explains how to store your local LLM weights, artifacts, and license metadata in a private Google Cloud Storage bucket and how to download them (for example in Colab) for testing.

Security first

- Never commit service account keys to version control.
- Prefer using signed URLs for short-term access.

Step 1 — Create your GCS bucket

1. Create a bucket

```bash
gcloud storage buckets create gs://goblin-assistant-llm --location=us-central1 --uniform-bucket-level-access
```

Make it private (default). If you want public access for the models, restrict to a specific prefix only (not recommended).

Step 2 — Create a service account (optional, or for automation)

```bash

gcloud iam service-accounts create colab-reader --display-name="Colab GCS Reader"
gcloud projects add-iam-policy-binding $PROJECT_ID \\
  --member="serviceAccount:colab-reader@$PROJECT_ID.iam.gserviceaccount.com" \\
  --role=roles/storage.objectViewer
gcloud iam service-accounts keys create colab-reader-key.json \\
  --iam-account=colab-reader@$PROJECT_ID.iam.gserviceaccount.com
```
Store `colab-reader-key.json` securely and do not commit it.

Step 3 — Uploading artifacts

This repo includes a utility script to upload model files and licenses into the bucket with resumable uploads:

```bash
python tools/llm_storage/upload_model.py --bucket goblin-assistant-llm --src ./models/7b --dest models/7b --licenses ./licenses
```

Options:

- `--src`: local file or directory to upload
- `--dest`: destination prefix in the bucket
- `--licenses`: optional directory of license files to upload under `<dest>/licenses`
- `--signed-url`: prints signed URLs after upload (requires service account credentials set in `GOOGLE_APPLICATION_CREDENTIALS`)

Step 4 — Downloading in Colab (example)
Two options:

- Signed URL (short-term): Use `--signed-url` to generate URLs and copy/paste them in Colab.
- Service Account: Upload `colab-reader-key.json` into Colab and run the sample code in `tools/llm_storage/colab_download_test.py`.

Security & Best practices

- Use signed URLs whenever possible for temporary access.
- Rotate keys regularly and set least-privilege IAM roles.
- Keep the bucket private; only grant `storage.objectViewer` to the service account used by Colab and automation.

Troubleshooting

- If upload fails with 403 or 404, check your service account permissions and bucket name.
- For very large models (>1GB), the uploader uses resumable uploads — make sure the network is stable.

---


## Google Drive alternative


If you prefer Google Drive for quick sharing or Colab workflows instead of GCS, follow the steps below.

1. Create a folder in your Drive to host the models. Note the `FOLDER_ID` from the URL.

2. Option 1 (Service Account): Create a service account, share the folder with the service account email, set `GOOGLE_APPLICATION_CREDENTIALS` to the service account JSON and run:

```bash

python tools/llm_storage/upload_model_gdrive.py --folder-id <FOLDER_ID> --src ./models/7b
```

1. Option 2 (OAuth): Use an OAuth flow (not covered here) to authorize the uploader with your user account.
2. In Colab, download files using `tools/llm_storage/colab_download_gdrive.py --folder-id <FOLDER_ID>` after setting `GOOGLE_APPLICATION_CREDENTIALS` or by using shared URLs.

Notes:

- Public sharing: Use `--share public` to set permission to `anyone with link` on uploaded files.
- Service Account: Keep the JSON file private and only use least-privilege roles.
- Licenses: Use `--licenses` to upload a directory of license files under the `licenses/` subfolder in the model folder.
