import numpy as np
from django.core.files import File
from io import BytesIO
import face_recognition
from PIL import Image, ImageDraw


"""
    The business logic of the project
"""


class FaceCompare:
    """
        The class responsible for the logic of searching for similar faces
    """
    def __init__(self, img, data):
        """
            :param img: Picture with faces
            :param key_img_name: list of models to search for
        """
        self.data = data
        self.img = img

        self.img_load = face_recognition.load_image_file(img)
        # self.img_faces_encoding = face_recognition.face_encodings(self.img_load)
        self.img_faces_locate = face_recognition.face_locations(self.img_load)

        # self.img_selection_faces = self._selection_faces()
        self.imgs_extracting_faces = self._extracting_faces()

    def _selection_faces(self):
        """
            Highlighting faces in a photo
        """
        pil_img = Image.fromarray(self.img_load)
        draw = ImageDraw.Draw(pil_img)

        for face_locations in self.img_faces_locate:
            top, right, botton, left = face_locations

            draw.rectangle(((left, top), (right, botton)), outline=(255, 255, 0), width=2)

        del draw

        img_io = BytesIO()  # create a BytesIO object
        pil_img.save(img_io, 'PNG')  # save image to BytesIO object
        img_selection_faces = File(img_io, f'selection_faces.png')  # create a django friendly File object

        return img_selection_faces

    def _extracting_faces(self):
        """
            Cuts faces with photos

            :return: coordinate dictionary: face_encoding
        """
        faces = []
        locations = []

        for face_locations in self.img_faces_locate:
            info = []

            top, right, botton, left = face_locations

            face_img = self.img_load[top:botton, left:right]
            pil_img = Image.fromarray(face_img)

            img_io = BytesIO()  # create a BytesIO object
            pil_img.save(img_io, 'PNG')  # save image to BytesIO object
            img_selection_faces = File(img_io, f'{face_locations}.png')  # create a django friendly File object

            info.append(img_selection_faces)
            info.append(face_recognition.face_encodings(face_recognition.load_image_file(img_selection_faces))[0])

            faces.append(info)
            locations.append(f'{left}:{right}, {top}:{botton}')

        return dict(zip(locations, faces))

    def compare(self):
        """
            Compares clipped faces with faces from data list

            :return: list which consists of dictionaries - coordinates of faces: matches from data
        """

        answer = []
        faces_encoding = []

        for data in self.data:
            face_encoding = np.array([np.float64(item) for item in data.face_encoding.split()])
            faces_encoding.append(face_encoding)

        for locate in self.imgs_extracting_faces:
            result_compare = face_recognition.compare_faces(faces_encoding, self.imgs_extracting_faces[locate][1], 0.45)

            result_face = []

            for i in range(len(result_compare)):
                if result_compare[i]:
                    result_face.append(self.data[i])

            answer.append(
                {
                    "coordinates": locate,
                    "coincidences": result_face
                }
            )

        return answer

    @staticmethod
    def get_img_encoding(face):
        """
            Calculation of encoding for all faces in the picture

            :param face: the path to the photo
            :return: encoding list for all faces in the picture
        """
        img = face_recognition.load_image_file(face)
        img_encoding = face_recognition.face_encodings(img)

        return img_encoding

    @staticmethod
    def get_img_encoding_str(face):
        """
            Calculation of encoding for one face in a photo (for example, if it is a photo from documents)

            :param face: the path to the photo
            :return: encoding string
        """
        img = face_recognition.load_image_file(face)
        img_encoding = face_recognition.face_encodings(img)

        img_encoding_list = list(img_encoding[0])

        img_encoding_str = ""
        for item in img_encoding_list:
            img_encoding_str += str(item) + " "

        return img_encoding_str
