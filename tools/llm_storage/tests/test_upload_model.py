import os
from pathlib import Path
from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def patch_storage_client(monkeypatch):
    class DummyBlob:
        def __init__(self, name):
            self.name = name
            self.chunk_size = None

        def upload_from_filename(self, filename, timeout=None):
            # simulate an upload by checking file exists
            assert Path(filename).exists()
            return True

        def download_to_filename(self, filename):
            Path(filename).write_text('dummy')

    class DummyBucket:
        def __init__(self, name):
            self.name = name

        def exists(self):
            return True

        def blob(self, name):
            return DummyBlob(name)

    class DummyClient:
        def __init__(self):
            self.bucket_name = None

        def bucket(self, name):
            return DummyBucket(name)

        def list_blobs(self, bucket_name, prefix):
            # return an iterable with a dummy object
            class DummyB:
                def __init__(self, name):
                    self.name = name

            return [DummyB(prefix + '/file.bin')]

    # Ensure google.cloud.storage exists in sys.modules for import
    import types, sys
    storage_module = types.ModuleType('google.cloud.storage')
    storage_module.Client = lambda: DummyClient()
    google_cloud_module = types.ModuleType('google.cloud')
    # Put our storage module into google.cloud
    google_cloud_module.storage = storage_module
    sys.modules['google'] = types.ModuleType('google')
    sys.modules['google.cloud'] = google_cloud_module
    sys.modules['google.cloud.storage'] = storage_module
    yield


def test_upload_single_file(tmp_path, capsys):
    # create a small file
    f = tmp_path / 'mymodel.bin'
    f.write_text('content')
    # import the uploader and run
    import importlib
    uploader = importlib.import_module('tools.llm_storage.upload_model')

    rc = uploader.main(['--bucket', 'mybucket', '--src', str(f), '--dest', 'models/1'])
    assert rc == 0


def test_upload_dir_and_licenses(tmp_path):
    models_dir = tmp_path / 'models'
    models_dir.mkdir()
    (models_dir / 'weights.bin').write_text('abc')

    licenses = tmp_path / 'licenses'
    licenses.mkdir()
    (licenses / 'license.txt').write_text('MIT')

    import importlib
    uploader = importlib.import_module('tools.llm_storage.upload_model')
    rc = uploader.main(['--bucket', 'mybucket', '--src', str(models_dir), '--dest', 'models/2', '--licenses', str(licenses)])
    assert rc == 0
