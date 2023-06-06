import hashlib
import os
import typing as t
from collections import namedtuple

GIT_DIR = ".ugit"


def init():
    os.makedirs(GIT_DIR)
    os.makedirs(f"{GIT_DIR}/objects")


RefValue = namedtuple("RefValue", ["symbolic", "value"])


def update_ref(ref: str, value: "RefValue"):
    assert not value.symbolic
    ref = _get_ref_internal(ref)[0]
    ref_path = f"{GIT_DIR}/{ref}"
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, "w") as f:
        f.write(value.value)


def get_ref(ref: str) -> "RefValue":
    return _get_ref_internal(ref)[1]


def _get_ref_internal(ref: str) -> t.Tuple[str, "RefValue"]:
    ref_path = f"{GIT_DIR}/{ref}"
    value = None
    if os.path.isfile(ref_path):
        with open(ref_path) as f:
            value = f.read().strip()

    symbolic = bool(value) and value.startswith('ref:')
    if symbolic:
        value = value.split(':', 1)[1].strip()
        return _get_ref_internal(value)

    return ref, RefValue(symbolic=False, value=value)


def iter_refs():
    refs = ["HEAD"]
    for root, _, filenames in os.walk(f"{GIT_DIR}/refs/"):
        # 拿到以 refs/ 开头的名字
        root = os.path.relpath(root, GIT_DIR)
        refs.extend(f"{root}/{name}" for name in filenames)

    for refname in refs:
        yield refname, get_ref(refname)


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
