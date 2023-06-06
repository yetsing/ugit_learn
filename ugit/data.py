import hashlib
import os
import typing as t

GIT_DIR = ".ugit"


def init():
    os.makedirs(GIT_DIR)
    os.makedirs(f"{GIT_DIR}/objects")


def update_ref(ref: str, oid: str):
    with open(f"{GIT_DIR}/{ref}", "w") as f:
        f.write(oid)


def get_ref(ref: str) -> str:
    if os.path.isfile(f"{GIT_DIR}/{ref}"):
        with open(f"{GIT_DIR}/{ref}") as f:
            return f.read().strip()


def hash_object(data: bytes, type_: str = "blob") -> str:
    obj = type_.encode() + b"\x00" + data
    oid = hashlib.sha1(obj).hexdigest()
    with open(f"{GIT_DIR}/objects/{oid}", "wb") as out:
        out.write(obj)
    return oid


def get_object(oid: str, expected: t.Optional[str] = "blob") -> bytes:
    with open(f"{GIT_DIR}/objects/{oid}", "rb") as f:
        obj = f.read()

    type_, _, content = obj.partition(b"\x00")
    type_ = type_.decode()

    if expected is not None:
        assert type_ == expected, f"Expected {expected}, got {type_}"
    return content
