"""Tests for local-only Zotero MCP client boundaries and contracts."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from conftest import DummyContext, FakeZotero

from zotero_mcp import client, server
from zotero_mcp.tools import _helpers


class TestLocalOnlyClientContracts:
    """Contract 1: Even with ZOTERO_API_KEY present, only local=True client is built."""

    def test_client_always_local_even_with_web_env(self, monkeypatch):
        monkeypatch.setenv("ZOTERO_API_KEY", "secret_web_key")
        monkeypatch.setenv("ZOTERO_LIBRARY_ID", "99999")
        monkeypatch.setenv("ZOTERO_LIBRARY_TYPE", "user")
        monkeypatch.setenv("ZOTERO_LOCAL", "true")

        # mock load_local_key to return dummy local credentials
        monkeypatch.setattr(
            "pyzotero._helpers.load_local_key",
            lambda: ("dummy-server-id", "dummy-local-key"),
        )

        c = client.get_zotero_client()
        assert c.local is True
        assert c.endpoint == "http://localhost:23119/api"
        # Web api_key must not be passed to local client
        assert c.api_key is None

    def test_local_write_client_has_local_api_key(self, monkeypatch):
        monkeypatch.setattr(
            "pyzotero._helpers.load_local_key",
            lambda: ("dummy-server-id", "dummy-local-key"),
        )

        wc = client.get_local_write_client()
        assert wc.local is True
        assert wc.endpoint == "http://localhost:23119/api"
        assert wc.local_api_key == "dummy-local-key"
        assert wc._server_id == "dummy-server-id"


class TestNoLocalKeyFailsClearly:
    """Contract 2: Without local write key, write operations fail with exact message."""

    def test_missing_local_key_raises_informative_error(self, monkeypatch):
        monkeypatch.setattr(
            "pyzotero._helpers.load_local_key",
            lambda: (None, None),
        )

        with pytest.raises(RuntimeError) as exc_info:
            client.get_local_write_client()

        err_msg = str(exc_info.value)
        assert "No local Zotero write key" in err_msg
        assert "pyzotero authorize" in err_msg
        assert "Always Allow" in err_msg


class TestLocalClientUsedForOperations:
    """Contract 3: Item movement and metadata updates use local client."""

    def test_manage_collections_uses_local_client(self, monkeypatch):
        fake_local_read = FakeZotero()
        fake_local_write = FakeZotero()
        fake_local_write.added_to_collections = []
        fake_local_write.removed_from_collections = []

        fake_local_read._items = [
            {"key": "ITEM0001", "version": 1, "data": {"title": "Paper 1", "collections": ["ABC00001"]}}
        ]
        fake_local_read._collections = [
            {"key": "ABC00001", "data": {"name": "Col 1", "parentCollection": False}},
            {"key": "ABC00002", "data": {"name": "Col 2", "parentCollection": False}},
        ]
        fake_local_write._items = fake_local_read._items

        def fake_addto(key, items, **kwargs):
            fake_local_write.added_to_collections.append((key, items))
            from tests.test_collections import _FakeResponse
            return _FakeResponse(204)

        def fake_delfrom(key, item, **kwargs):
            fake_local_write.removed_from_collections.append((key, item))
            from tests.test_collections import _FakeResponse
            return _FakeResponse(204)

        fake_local_write.addto_collection = fake_addto
        fake_local_write.deletefrom_collection = fake_delfrom

        monkeypatch.setattr(
            "zotero_mcp.tools._helpers._get_write_client",
            lambda ctx: (fake_local_read, fake_local_write),
        )

        ctx = DummyContext()
        res = server.manage_collections(item_keys=["ITEM0001"], add_to=["ABC00002"], ctx=ctx)
        assert len(fake_local_write.added_to_collections) == 1
        assert fake_local_write.added_to_collections[0][0] == "ABC00002"


class TestAttachmentsNoWebOrDirectWebDAV:
    """Contract 4: Attachment reading and writing do not call Web API or direct WebDAV."""

    def test_download_attachment_file_signature_and_no_web(self, tmp_path):
        fake_local = FakeZotero()
        dest_file = tmp_path / "test.pdf"

        def fake_dump(key, filename=None, path=None):
            dest_file.write_bytes(b"%PDF-fake")

        fake_local.dump = MagicMock(side_effect=fake_dump)

        res = client.download_attachment_file(
            attachment_key="ATT1",
            destination_dir=tmp_path,
            filename="test.pdf",
            local_client=fake_local,
        )

        assert res.path == dest_file
        assert res.source == "Local Zotero"

    def test_attach_and_verify_calls_local_upload_attachments(self, tmp_path):
        sample_pdf = tmp_path / "sample.pdf"
        sample_pdf.write_bytes(b"%PDF-1.4 mock content")

        fake_local_write = FakeZotero()
        fake_local_write.upload_attachments = MagicMock(return_value={
            "success": [{"key": "ATT123", "filename": "sample.pdf"}],
            "failure": [],
            "unchanged": [],
        })
        fake_local_read = FakeZotero()
        fake_local_read.children = MagicMock(return_value=[
            {"key": "ATT123", "data": {"itemType": "attachment", "md5": "dummy_md5"}}
        ])

        ok, suffix, att_key = _helpers._attach_and_verify(
            write_zot=fake_local_write,
            filename="sample.pdf",
            file_path=str(sample_pdf),
            parent_key="ITEM0123",
            ctx=DummyContext(),
        )

        assert ok is True
        assert att_key == "ATT123"
        fake_local_write.upload_attachments.assert_called_once()
