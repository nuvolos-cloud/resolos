import jwt
import requests
from ..exception import ResolosException, YaretaError
from ..logging import clog
from ..config import get_option
from time import sleep

DOWNLOAD_CHUNK_SIZE = 8192


class YaretaClient(object):
    def __init__(self, base_url, access_token):
        self.base_url = base_url
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {access_token}"})

    def request(self, method, path, expected_status_code=None, **kwargs):
        url = f"{self.base_url}{path}"
        resp = self.session.request(method, url, timeout=15, **kwargs)
        if resp.status_code == 401:
            raise YaretaError(
                f"Received 'Unauthorized' response from the server for request [{method}] {url}\n"
                f"Has your access token expired? Try generating a new one"
            )
        if (
            expected_status_code is not None
            and resp.status_code != expected_status_code
        ):
            raise YaretaError(
                f"Expected response code {expected_status_code} for request [{method}] {url}, "
                f"received {resp}"
            )
        return resp

    def get(self, path, expected_status_code=None, **kwargs):
        return self.request(
            "GET", path, expected_status_code=expected_status_code, **kwargs
        )

    def post(self, path, expected_status_code=None, **kwargs):
        return self.request(
            "POST", path, expected_status_code=expected_status_code, **kwargs
        )


def get_uid_from_token(access_token: str):
    d = jwt.decode(access_token, options={"verify_signature": False})
    username = d.get("user_name")
    if username is None:
        raise ResolosException(
            f"Invalid access token format: expected field 'user_name' to be present"
        )
    return username


def get_person_res_id(yc: YaretaClient, username: str):
    resp = yc.get(
        "/administration/admin/users",
        expected_status_code=200,
        params={"externalUid": username},
    )
    data = resp.json()
    found_username = data["_data"][0]["externalUid"]
    if found_username != username:
        raise ResolosException(
            f"Could not find user by externalUid '{username}', "
            f"as the returned user's externalUid is {found_username}"
        )
    return data["_data"][0]["person"]["resId"]


def create_deposit(
    yc: YaretaClient,
    org_unit_id,
    title,
    year,
    description,
    authors,
    access,
    license_id,
    keywords,
):
    if keywords is None:
        keywords = []
    resp = yc.post(
        "/ingestion/preingest/deposits",
        expected_status_code=201,
        json={
            "organizationalUnitId": org_unit_id,
            "title": title,
            "description": description,
            "year": year,
            "access": access,
            "licenseId": license_id,
            "keywords": keywords,
        },
    )
    deposit_res = resp.json()
    deposit_id = deposit_res["resId"]
    res = set_deposit_contributors(yc, deposit_id, authors)
    clog.info(f"Successfully created deposit '{deposit_id}' with title '{title}'")
    return deposit_res


def set_deposit_contributors(yc: YaretaClient, deposit_id, authors):
    resp = yc.post(
        f"/ingestion/preingest/deposits/{deposit_id}/contributors",
        expected_status_code=201,
        json=authors,
    )
    clog.debug(f"Successfully updated contributors of deposit'{deposit_id}'")
    res = resp.json()
    return res


def upload_file_to_deposit(yc: YaretaClient, deposit_id, filename):
    with open(filename, "rb") as f:
        resp = yc.post(
            f"/ingestion/preingest/deposits/{deposit_id}/upload",
            expected_status_code=200,
            files={"file": f},
        )
    res = resp.json()
    clog.info(f"Successfully uploaded file '{filename}' to deposit '{deposit_id}'")
    return res


def approve_deposit(yc: YaretaClient, deposit_id):
    resp = yc.post(
        f"/ingestion/preingest/deposits/{deposit_id}/approve", expected_status_code=200
    )
    res = resp.json()
    clog.info(f"Successfully submitted deposit '{deposit_id}'")
    return res


def deposit_archive(
    archive_filename: str,
    base_url: str,
    access_token: str,
    org_unit_id: str,
    title: str,
    year: str,
    description: str,
    **kwargs,
):
    access = get_option(kwargs, "access")
    license_id = get_option(kwargs, "license_id")
    keywords = get_option(kwargs, "keywords", split_list=True)
    yc = YaretaClient(base_url, access_token)
    username = get_uid_from_token(access_token)
    person_res_id = get_person_res_id(yc, username)
    clog.debug(
        f"Found Yareata username {username} from access token, person resId is {person_res_id}"
    )
    res = create_deposit(
        yc,
        org_unit_id,
        title,
        year,
        description,
        [person_res_id],
        access,
        license_id,
        keywords,
    )
    deposit_id = res["resId"]
    upload_file_to_deposit(yc, deposit_id, archive_filename)
    sleep(10)
    approve_deposit(yc, deposit_id)
    return deposit_id


def search_deposit(yc: YaretaClient, deposit_id, archive_filename):
    full_file_name = f"/{archive_filename}"
    resp = yc.get(
        f"/ingestion/preingest/deposits/{deposit_id}/data",
        expected_status_code=200,
    )
    data = resp.json()
    results = data["_data"]
    if len(results) != 2:
        raise ResolosException(
            f"Expected 2 files in deposit '{deposit_id}': the archive file {full_file_name} and the metadata XML. "
            f"Are you sure this deposit was created by Resolos?"
        )
    file_id = None
    for r in results:
        if r["fullFileName"] == full_file_name:
            file_id = r["resId"]
    if file_id is None:
        raise ResolosException(
            f"Could not find file '{full_file_name}' in deposit '{deposit_id}'. "
            f"Are you sure this deposit was created by Resolos?"
        )
    clog.debug(
        f"Found file '{archive_filename}' with id '{file_id}' in deposit '{deposit_id}'"
    )
    return file_id


def download_file(yc, deposit_id, file_id, target_filename):
    r = yc.get(
        f"/ingestion/preingest/deposits/{deposit_id}/data/{file_id}/download",
        expected_status_code=200,
        stream=True,
    )
    try:
        clog.info(f"Downloading file '{file_id}'...")
        with open(target_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                f.write(chunk)
        clog.info(f"Successfully downloaded file '{file_id}' to '{target_filename}'")
        return target_filename
    finally:
        r.close()


def download_archive(
    target_filename: str,
    archive_filename: str,
    deposit_id: str,
    access_token: str,
    base_url: str,
):

    yc = YaretaClient(base_url, access_token)
    file_id = search_deposit(yc, deposit_id, archive_filename)
    download_file(yc, deposit_id, file_id, target_filename)
