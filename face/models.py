import io
import zipfile

from django.db import models

from services import FaceCompare


def load_data(photo, info):
    """
        Loads data into the database from a user. Checks if there is such a person and which table the record belongs to
        :param photo: zipfile с фотками
        :param info: txt c инфой
        :return: информацию о количестве загруженных записей и ошибки
    """
    from api.serializers import STATUS, DETAIL

    successful_entries = 0
    erroneous_entries = 0
    error_record = []

    with zipfile.ZipFile(io.BytesIO(photo.read()), 'r') as zf:
        for line in info:

            record = line.decode('utf-8').split('[%]')[:-1]

            if record[len(record) - 1] in zf.namelist():

                face_encoding = FaceCompare.get_img_encoding_str(zf.open(record[len(record) - 1]))

                try:
                    face = FaceModel.objects.get(face_encoding=face_encoding)
                except FaceModel.DoesNotExist:
                    face = FaceModel.objects.create(face_encoding=face_encoding)

                if record[0] in DocumentModel.Source:
                    document = DocumentModel.objects.create(
                        source=record[0],
                        document_number=record[1],
                        name=record[2]
                    )

                    a = RelatedModel.objects.create(
                        face=face,
                        table_name=RelatedModel.TableName.DOCUMENT,
                        record_id=document.id,
                    )

                    successful_entries += 1

                elif record[0] in AvatarModel.Source:
                    avatar = AvatarModel.objects.create(
                        source=record[0],
                        profile_id=record[1],
                        name=record[2]
                    )

                    RelatedModel.objects.create(
                        face=face,
                        table_name=RelatedModel.TableName.AVATAR,
                        record_id=avatar.id,
                    )

                    successful_entries += 1

                else:
                    erroneous_entries += 1
                    error_record.append({
                        "name_record": " ".join(record),
                        "type_error": DETAIL[2]
                    })

            else:
                erroneous_entries += 1
                error_record.append({
                    "name_record": " ".join(record),
                    "type_error": DETAIL[1]
                })

    return {
        'status': STATUS[0],
        'number_successful_entries': successful_entries,
        'number_erroneous_entries': erroneous_entries,
        'detail_error_list': error_record,
    }


class FaceModel(models.Model):
    """
        Face model
    """
    face_encoding = models.TextField()

    class Meta:
        verbose_name = "Обличче"
        verbose_name_plural = "Обличчя"
        ordering = ["id"]

    @staticmethod
    def get_info_on_faces(faces_on_upload_img):
        """
            Getting information about face matches from business logic. That is, collecting information about the face
            model

            :param faces_on_upload_img: инфа из бизнес логики (спискок словарей координаты:list(совпадения))
        """
        for face_in_img in faces_on_upload_img:
            documents, avatars = [], []
            for face_model in face_in_img['coincidences']:
                relations = face_model.related.all()

                for related in relations:
                    if related.table_name == RelatedModel.TableName.DOCUMENT:
                        document = DocumentModel.objects.get(id=related.record_id)
                        documents.append(document)

                    if related.table_name == RelatedModel.TableName.AVATAR:
                        avatar = AvatarModel.objects.get(id=related.record_id)
                        avatars.append(avatar)

            face_in_img['info'] = {
                'documents': documents,
                'avatars': avatars,
            }


class RelatedModel(models.Model):
    """
        Linkage model
    """
    class TableName(models.TextChoices):
        """
            What tablets the facial model can be related to
        """
        DOCUMENT = "face_documentmodel", "Документи"
        AVATAR = "face_avatarmodel", "Аватари"

    face = models.ForeignKey(
        FaceModel,
        on_delete=models.CASCADE,
        related_name='related'
    )

    table_name = models.CharField(
        choices=TableName.choices,
        max_length=100
    )

    record_id = models.BigIntegerField()

    class Meta:
        verbose_name = "Зв'язок"
        verbose_name_plural = "Зв'язки"
        ordering = ["id"]

    def __str__(self):
        return f"face:{self.face}; table_name:{self.table_name}; id_record:{self.record_id};"


class DocumentModel(models.Model):
    """
        Document model
    """
    class Source(models.TextChoices):
        """
            Possible data sources. New ones must be prescribed here! You can remove it, but then you will be able to
            any entry in the model (you need to remove selections in the source).
        """
        password = "passport", "Паспорт"
        driver_license = "driver_license", "Водительские удостоверение"

    source = models.CharField(
        choices=Source.choices,
        max_length=100
    )

    document_number = models.CharField(max_length=100)

    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документи"
        ordering = ["id"]

    def __str__(self):
        return f"source:{self.source}; document_number:{self.document_number}; name:{self.name};"


class AvatarModel(models.Model):
    """
        Model avatars
    """
    class Source(models.TextChoices):
        """
            Possible data sources. New ones must be prescribed here! You can remove it, but then you will be able to
            any entry in the model (you need to remove selections in the source).
        """
        vk = "vk", "ВКонтакте"
        ok = "ok", "Одноклассники"
        tg = "tg", "Телеграм"
        fb = "fb", "Фейсбук"
        viber = "viber", "Вайбер"

    source = models.CharField(
        choices=Source.choices,
        max_length=100
    )

    profile_id = models.CharField(max_length=100)

    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Аватар"
        verbose_name_plural = "Аватари"
        ordering = ["id"]

    def __str__(self):
        return f"source:{self.source}; profile_id:{self.profile_id}; name:{self.name};"
