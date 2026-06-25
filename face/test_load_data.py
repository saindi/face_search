"""
Tests for face.models.load_data — the bulk import that ingests a zip of
photos plus a text manifest and writes Face/Document/Avatar/Related rows.

FaceCompare.get_img_encoding_str is mocked so no real face encoding runs;
the zip and manifest are built in-memory.
"""
import io
import zipfile
from unittest import mock

from django.test import TestCase

from api.serializers import DETAIL, STATUS
from face.models import (
    AvatarModel,
    DocumentModel,
    FaceModel,
    RelatedModel,
    load_data,
)


def _zip_with(*names):
    """A file-like zip archive containing an entry for each given name."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name in names:
            zf.writestr(name, b"not-a-real-image")
    return io.BytesIO(buf.getvalue())


def _info(*records):
    """Encode manifest lines; each record is (source, number, name, filename)."""
    return ["[%]".join(record).encode("utf-8") + b"[%]" for record in records]


@mock.patch(
    "face.models.FaceCompare.get_img_encoding_str", return_value="0.1 0.2 0.3"
)
class LoadDataTests(TestCase):
    def test_loads_a_document_record(self, _enc):
        result = load_data(
            _zip_with("john.png"),
            _info(("passport", "AA123", "John", "john.png")),
        )

        self.assertEqual(result["status"], STATUS[0])
        self.assertEqual(result["number_successful_entries"], 1)
        self.assertEqual(result["number_erroneous_entries"], 0)
        self.assertEqual(result["detail_error_list"], [])

        self.assertEqual(FaceModel.objects.count(), 1)
        document = DocumentModel.objects.get()
        self.assertEqual(document.source, "passport")
        self.assertEqual(document.document_number, "AA123")
        self.assertEqual(document.name, "John")

        related = RelatedModel.objects.get()
        self.assertEqual(related.table_name, RelatedModel.TableName.DOCUMENT)
        self.assertEqual(related.record_id, document.id)
        self.assertEqual(related.face, FaceModel.objects.get())

    def test_loads_an_avatar_record(self, _enc):
        result = load_data(
            _zip_with("olha.png"),
            _info(("vk", "9981", "Olha", "olha.png")),
        )

        self.assertEqual(result["number_successful_entries"], 1)
        avatar = AvatarModel.objects.get()
        self.assertEqual(avatar.source, "vk")
        self.assertEqual(avatar.profile_id, "9981")
        self.assertEqual(avatar.name, "Olha")

        related = RelatedModel.objects.get()
        self.assertEqual(related.table_name, RelatedModel.TableName.AVATAR)
        self.assertEqual(related.record_id, avatar.id)

    def test_unknown_source_is_recorded_as_an_error(self, _enc):
        result = load_data(
            _zip_with("z.png"),
            _info(("myspace", "1", "Z", "z.png")),
        )

        self.assertEqual(result["number_successful_entries"], 0)
        self.assertEqual(result["number_erroneous_entries"], 1)
        self.assertEqual(result["detail_error_list"][0]["type_error"], DETAIL[2])

        # The face is still created before the source is validated, but no
        # document/avatar/relation is written for an unknown source.
        self.assertEqual(FaceModel.objects.count(), 1)
        self.assertEqual(DocumentModel.objects.count(), 0)
        self.assertEqual(AvatarModel.objects.count(), 0)
        self.assertEqual(RelatedModel.objects.count(), 0)

    def test_missing_image_is_recorded_as_an_error(self, enc):
        result = load_data(
            _zip_with("present.png"),
            _info(("passport", "1", "Z", "absent.png")),
        )

        self.assertEqual(result["number_successful_entries"], 0)
        self.assertEqual(result["number_erroneous_entries"], 1)
        self.assertEqual(result["detail_error_list"][0]["type_error"], DETAIL[1])

        # The encoding is never computed for a record whose photo is missing.
        enc.assert_not_called()
        self.assertEqual(FaceModel.objects.count(), 0)

    def test_identical_encoding_reuses_a_single_face(self, _enc):
        result = load_data(
            _zip_with("a.png", "b.png"),
            _info(
                ("passport", "1", "A", "a.png"),
                ("vk", "2", "B", "b.png"),
            ),
        )

        self.assertEqual(result["number_successful_entries"], 2)
        self.assertEqual(FaceModel.objects.count(), 1)
        self.assertEqual(RelatedModel.objects.count(), 2)
        self.assertEqual(DocumentModel.objects.count(), 1)
        self.assertEqual(AvatarModel.objects.count(), 1)

    def test_mixed_batch_counts_successes_and_errors(self, _enc):
        result = load_data(
            _zip_with("ok.png", "bad.png"),
            _info(
                ("passport", "1", "Valid", "ok.png"),
                ("myspace", "2", "BadSource", "bad.png"),
                ("vk", "3", "Missing", "gone.png"),
            ),
        )

        self.assertEqual(result["number_successful_entries"], 1)
        self.assertEqual(result["number_erroneous_entries"], 2)
        self.assertEqual(len(result["detail_error_list"]), 2)
