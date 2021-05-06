import jwt
import requests
from ..exception import ResolosException
from ..logging import clog
from time import sleep


YARETA_BASE_URL = "https://sandbox.dlcm.ch"


class YaretaClient(object):
    def __init__(self, base_url, access_token):
        self.base_url = base_url
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {access_token}"})

    def request(self, method, path, expected_status_code=None, **kwargs):
        url = f"{self.base_url}{path}"
        resp = self.session.request(method, url, **kwargs)
        if resp.status_code == 401:
            raise ResolosException(
                f"Received 'Unauthorized' response from the server for request [{method}] {url}\n"
                f"Has your access token expired? Try generating a new one"
            )
        if (
            expected_status_code is not None
            and resp.status_code != expected_status_code
        ):
            raise ResolosException(
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


def get_option(d: dict, key: str, err_msg: str = None, split_list=False):
    res = d.get(key)
    if res is not None or err_msg is None:
        if split_list:
            return [c.strip() for c in res.split(",")]
        else:
            return res
    else:
        raise ResolosException(err_msg)


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


def deposit_archive(archive_filename: str, **kwargs):
    access_token = get_option(kwargs, "access_token", f"No access token was found")
    org_unit_id = get_option(
        kwargs, "organizational_unit_id", f"No organizational unit id was found"
    )
    title = get_option(kwargs, "title", f"No Yareta deposit title was specified")
    year = get_option(kwargs, "year", f"No Yareta deposit year was specified")
    description = get_option(
        kwargs, "description", f"No Yareta deposit description was specified"
    )
    access = get_option(kwargs, "access")
    license_id = get_option(kwargs, "license_id")
    keywords = get_option(kwargs, "keywords", split_list=True)
    yc = YaretaClient(YARETA_BASE_URL, access_token)
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


def download_archive(reqid: str):
    pass
