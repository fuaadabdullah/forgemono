---
title: "LLM STORAGE"
description: "Documentation for LLM STORAGE"
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
