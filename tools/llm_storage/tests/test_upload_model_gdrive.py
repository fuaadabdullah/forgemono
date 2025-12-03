import os
from pathlib import Path
from unittest import mock
import types

import pytest


@pytest.fixture(autouse=True)
def patch_drive_service(monkeypatch, tmp_path):
    # Fake drive service with files().create() that 'uploads'
    class DummyFiles:
        def __init__(self):
            self._uploads = []

        def create(self, body=None, media_body=None, fields=None):
            class Req:
                def __init__(self, name):
                    self._name = name
                    self._done = False

                def next_chunk(self):
                    if not self._done:
                        self._done = True
                        return (None, {'id': 'id-' + self._name, 'webViewLink': 'http://drive/fake'})
                    return (None, None)

            return Req(body['name'])

    class DummyFilesService:
        def __init__(self):
            self._files = DummyFiles()

        def list(self, q=None, spaces=None, fields=None, pageSize=None):
            return types.SimpleNamespace(execute=lambda: {'files': []})

        def create(self, body=None, fields=None, media_body=None):
            # If media_body provided, simulate resumable upload request behavior
            if media_body is not None:
                class Req:
                    def __init__(self, name):
                        self._name = name
                        self._done = False

                    def next_chunk(self):
                        if not self._done:
                            self._done = True
                            return (None, {'id': 'id-' + self._name, 'webViewLink': 'http://drive/fake'})
                        return (None, None)

                return Req(body['name'])
            return types.SimpleNamespace(execute=lambda: {'id': 'folderid'})

    class DummyService:
        def __init__(self):
            self.files = lambda: DummyFilesService()

    def fake_build(service_name, version, credentials=None):
        return DummyService()

    import sys
    sys.modules['googleapiclient'] = types.ModuleType('googleapiclient')
    sys.modules['googleapiclient.discovery'] = types.ModuleType('googleapiclient.discovery')
    sys.modules['googleapiclient.discovery'].build = fake_build
    # stub http module with MediaFileUpload
    http_mod = types.ModuleType('googleapiclient.http')
    class MediaFileUpload:
        def __init__(self, filename, resumable=False, chunksize=None):
            self.filename = filename
            self.resumable = resumable
            self.chunksize = chunksize
    http_mod.MediaFileUpload = MediaFileUpload
    sys.modules['googleapiclient.http'] = http_mod
    sys.modules['google.oauth2'] = types.ModuleType('google.oauth2')
    sys.modules['google.oauth2.service_account'] = types.ModuleType('google.oauth2.service_account')
    class DummyCreds:
        @classmethod
        def from_service_account_file(cls, path, scopes=None):
            return None

    sys.modules['google.oauth2.service_account'].Credentials = DummyCreds

    yield


def test_upload_file_and_folder(tmp_path):
    # Prepare a sample file
    f = tmp_path / 'weights.bin'
    f.write_text('abc')
    import importlib
    uploader = importlib.import_module('tools.llm_storage.upload_model_gdrive')
    # Set a fake credentials path to avoid runtime error
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(tmp_path / 'fake.json')
    (tmp_path / 'fake.json').write_text('{}')
    rc = uploader.main(['--src', str(f), '--dest-folder', 'test-models'])
    assert rc == 0


def test_upload_with_licenses(tmp_path):
    models_dir = tmp_path / 'models'
    models_dir.mkdir()
    (models_dir / 'weights.bin').write_text('abc')
    licenses = tmp_path / 'licenses'
    licenses.mkdir()
    (licenses / 'license.txt').write_text('MIT')
    import importlib
    uploader = importlib.import_module('tools.llm_storage.upload_model_gdrive')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(tmp_path / 'fake.json')
    (tmp_path / 'fake.json').write_text('{}')
    rc = uploader.main(['--src', str(models_dir), '--licenses', str(licenses), '--dest-folder', 'test-models-2'])
    assert rc == 0
