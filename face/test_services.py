"""
Unit tests for the FaceCompare business logic in services.py.

The heavy native dependency (face_recognition / dlib) and the PIL image
plumbing are mocked at the module boundary so these tests exercise *our*
logic — face extraction bookkeeping, match mapping, tolerance handling and
encoding (de)serialisation — without needing real images or trained models.
"""
from unittest import mock

import numpy as np
from django.test import SimpleTestCase

from services import FaceCompare, DEFAULT_TOLERANCE


class _Record:
    """Minimal stand-in for FaceModel: only a face_encoding string is used."""

    def __init__(self, face_encoding="0.1 0.2 0.3"):
        self.face_encoding = face_encoding


def _fake_image():
    return np.zeros((8, 8, 3), dtype=np.uint8)


@mock.patch("services.File")
@mock.patch("services.Image")
@mock.patch("services.face_recognition")
class FaceCompareExtractionTests(SimpleTestCase):
    def test_faces_are_keyed_by_their_coordinates(self, fr, _image, _file):
        fr.load_image_file.return_value = _fake_image()
        # face_locations yields (top, right, botton, left) tuples.
        fr.face_locations.return_value = [(0, 4, 4, 0), (1, 7, 6, 2)]
        enc_a, enc_b = np.full(128, 0.1), np.full(128, 0.9)
        fr.face_encodings.side_effect = [[enc_a], [enc_b]]

        fc = FaceCompare("img.png", [])

        # locate string is f'{left}:{right}, {top}:{botton}'
        self.assertEqual(
            list(fc.imgs_extracting_faces.keys()),
            ["0:4, 0:4", "2:7, 1:6"],
        )
        np.testing.assert_array_equal(fc.imgs_extracting_faces["0:4, 0:4"][1], enc_a)
        np.testing.assert_array_equal(fc.imgs_extracting_faces["2:7, 1:6"][1], enc_b)

    def test_no_detected_faces_yields_empty_mapping(self, fr, _image, _file):
        fr.load_image_file.return_value = _fake_image()
        fr.face_locations.return_value = []

        fc = FaceCompare("img.png", [_Record()])

        self.assertEqual(fc.imgs_extracting_faces, {})
        self.assertEqual(fc.compare(), [])


@mock.patch("services.File")
@mock.patch("services.Image")
@mock.patch("services.face_recognition")
class FaceCompareMatchTests(SimpleTestCase):
    def _make(self, fr, *, locations, data):
        fr.load_image_file.return_value = _fake_image()
        fr.face_locations.return_value = locations
        fr.face_encodings.return_value = [np.zeros(128)]
        return FaceCompare("img.png", data)

    def test_truthy_results_are_mapped_back_to_records(self, fr, _image, _file):
        data = [_Record(), _Record(), _Record()]
        fr.compare_faces.return_value = [True, False, True]

        fc = self._make(fr, locations=[(0, 4, 4, 0)], data=data)
        answer = fc.compare()

        self.assertEqual(len(answer), 1)
        self.assertEqual(answer[0]["coordinates"], "0:4, 0:4")
        self.assertEqual(answer[0]["coincidences"], [data[0], data[2]])

    def test_no_matches_returns_empty_coincidences(self, fr, _image, _file):
        data = [_Record(), _Record()]
        fr.compare_faces.return_value = [False, False]

        fc = self._make(fr, locations=[(0, 4, 4, 0)], data=data)
        answer = fc.compare()

        self.assertEqual(answer[0]["coincidences"], [])

    def test_each_detected_face_is_compared(self, fr, _image, _file):
        data = [_Record()]
        fr.compare_faces.return_value = [True]

        fc = self._make(fr, locations=[(0, 4, 4, 0), (1, 7, 6, 2)], data=data)
        answer = fc.compare()

        self.assertEqual(len(answer), 2)
        self.assertEqual(fr.compare_faces.call_count, 2)

    def test_known_encodings_are_parsed_from_record_strings(self, fr, _image, _file):
        data = [_Record("0.1 0.2"), _Record("0.3 0.4")]
        fr.compare_faces.return_value = [False, False]

        fc = self._make(fr, locations=[(0, 4, 4, 0)], data=data)
        fc.compare()

        known = fr.compare_faces.call_args.args[0]
        self.assertEqual(len(known), 2)
        np.testing.assert_array_almost_equal(known[0], [0.1, 0.2])
        np.testing.assert_array_almost_equal(known[1], [0.3, 0.4])

    def test_default_tolerance_is_used(self, fr, _image, _file):
        fr.compare_faces.return_value = [False]

        fc = self._make(fr, locations=[(0, 4, 4, 0)], data=[_Record()])
        fc.compare()

        self.assertEqual(fr.compare_faces.call_args.args[2], DEFAULT_TOLERANCE)

    def test_custom_tolerance_is_forwarded(self, fr, _image, _file):
        fr.compare_faces.return_value = [False]

        fc = self._make(fr, locations=[(0, 4, 4, 0)], data=[_Record()])
        fc.compare(tolerance=0.3)

        self.assertEqual(fr.compare_faces.call_args.args[2], 0.3)


class EncodingHelperTests(SimpleTestCase):
    @mock.patch("services.face_recognition")
    def test_get_img_encoding_returns_every_face(self, fr):
        fr.load_image_file.return_value = _fake_image()
        encodings = [np.zeros(128), np.ones(128)]
        fr.face_encodings.return_value = encodings

        self.assertIs(FaceCompare.get_img_encoding("img.png"), encodings)

    @mock.patch("services.face_recognition")
    def test_get_img_encoding_str_serialises_first_face(self, fr):
        fr.load_image_file.return_value = _fake_image()
        fr.face_encodings.return_value = [np.array([0.1, 0.2, 0.3])]

        self.assertEqual(FaceCompare.get_img_encoding_str("img.png"), "0.1 0.2 0.3 ")

    @mock.patch("services.face_recognition")
    def test_get_img_encoding_str_round_trips(self, fr):
        original = np.array([0.123, -0.456, 0.789])
        fr.load_image_file.return_value = _fake_image()
        fr.face_encodings.return_value = [original]

        encoded = FaceCompare.get_img_encoding_str("img.png")
        parsed = np.array([np.float64(x) for x in encoded.split()])

        np.testing.assert_array_equal(parsed, original)
