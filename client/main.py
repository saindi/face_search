import zipfile
import psycopg2
from services import FaceCompare
import time


"""
    Mini client to load data into the database without djangp application.
"""


ZF_LICENSE_NAME = "test_files/photo.zip"
TXT_LICENSE_NAME = "test_files/info.txt"

DOCUMENT_TABLE = 'face_documentmodel'
AVATAR_TABLE = 'face_avatarmodel'

CHOICES_DOCUMENT = ['passport', 'driver_license']
CHOICES_AVATAR = ['vk', 'ok', 'tg', 'fb', 'viber']

STATUS = ['success', 'error']
DETAIL = ['На фото нема людей', 'Немає відповідності запису та фотографії', 'Незареєстрований вид джерела']


conn = psycopg2.connect(
    host="localhost",
    database="face_search_db",
    user="postgres",
    password="postgres"
)


def insert_record(data):
    cur = conn.cursor()

    for info in data:
        cur.execute(
            f"SELECT id FROM face_facemodel WHERE face_encoding='{info[len(info) - 1]}'"
        )

        face = cur.fetchall()

        if face:
            face_id = face[0][0]
        else:
            cur.execute(
                f"INSERT INTO face_facemodel (face_encoding) VALUES ('{info[len(info) - 1]}') RETURNING id"
            )
            conn.commit()

            face_id = cur.fetchall()[0][0]

        if info[0] in CHOICES_DOCUMENT:
            cur.execute(
                f"INSERT INTO face_documentmodel (source, document_number, name) VALUES (%s, %s, %s) RETURNING id",
                (info[0], info[1], info[2])
            )
            conn.commit()
            document_id = cur.fetchall()[0][0]

            cur.execute(
                f"INSERT INTO face_relatedmodel (face_id, table_name, record_id) "
                f"VALUES ({face_id}, '{DOCUMENT_TABLE}', {document_id}) RETURNING id"
            )
            conn.commit()

        elif info[0] in CHOICES_AVATAR:
            cur.execute(
                f"INSERT INTO face_avatarmodel (source, profile_id, name) VALUES (%s, %s, %s) RETURNING id",
                (info[0], info[1], info[2])
            )
            conn.commit()
            avatar_id = cur.fetchall()[0][0]

            cur.execute(
                f"INSERT INTO face_relatedmodel (face_id, table_name, record_id) "
                f"VALUES ({face_id}, '{AVATAR_TABLE}', {avatar_id}) RETURNING id"
            )
            conn.commit()

    cur.close()
    conn.close()


def processing_data():
    successful_entries = 0
    erroneous_entries = 0
    error_record = []

    data = []

    with open(TXT_LICENSE_NAME, 'r', encoding='utf-8') as file_txt:
        info = file_txt.read()

    with zipfile.ZipFile(ZF_LICENSE_NAME, 'r') as zf:
        info = info.split('\n')[:-1]
        for line in info:
            record = line.split('[%]')[:-1]

            if record[len(record) - 1] in zf.namelist():

                if record[0] in CHOICES_DOCUMENT:
                    record[len(record) - 1] = FaceCompare.get_img_encoding_str(zf.open(record[len(record) - 1]))

                    successful_entries += 1
                    data.append(record)

                elif record[0] in CHOICES_AVATAR:
                    record[len(record) - 1] = FaceCompare.get_img_encoding_str(zf.open(record[len(record) - 1]))

                    successful_entries += 1
                    data.append(record)

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

    info = {
        'number_successful_entries': successful_entries,
        'number_erroneous_entries': erroneous_entries,
        'detail_error_list': error_record,
    }

    print(f"Info: {info}")

    return data


def main():
    start_time = time.perf_counter()

    data = processing_data()

    insert_record(data)

    print(f"Lead time: {time.perf_counter() - start_time:.2f} sec")


if __name__ == "__main__":
    main()
