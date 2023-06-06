import itertools
import operator
import os
import typing as t
from collections import namedtuple

from . import data


def write_tree(directory="."):
    entryies = []
    with os.scandir(directory) as it:
        for entry in it:
            full = f"{directory}/{entry.name}"
            if is_ignored(full):
                continue
            if entry.is_file(follow_symlinks=False):
                type_ = "blob"
                with open(full, "rb") as f:
                    oid = data.hash_object(f.read())
            elif entry.is_dir(follow_symlinks=False):
                type_ = "tree"
                oid = write_tree(full)
            entryies.append((entry.name, oid, type_))

    tree = "".join(f"{type_} {oid} {name}\n" for name, oid, type_ in sorted(entryies))
    return data.hash_object(tree.encode(), "tree")


def _iter_tree_entries(oid: str):
    if not oid:
        return
    tree = data.get_object(oid, "tree")
    for entry in tree.decode().splitlines():
        type_, oid, name = entry.split(" ", 2)
        yield type_, oid, name


def get_tree(oid: str, base_path: str = "") -> t.Dict[str, str]:
    result = {}
    for type_, oid, name in _iter_tree_entries(oid):
        assert "/" not in name
        assert name not in ("..", ".")
        path = base_path + name
        if type_ == "blob":
            result[path] = oid
        elif type_ == "tree":
            result.update(get_tree(oid, f"{path}/"))
        else:
            assert False, f"Unknown tree entry {type_}"
    return result


def _empty_current_directory():
    for root, dirnames, filenames in os.walk(".", topdown=False):
        for filename in filenames:
            path = os.path.relpath(f"{root}/{filename}")
            if is_ignored(path) or not os.path.isfile(path):
                continue
            os.remove(path)
        for dirname in dirnames:
            path = os.path.relpath(f"{root}/{dirname}")
            if is_ignored(path):
                continue
            try:
                os.rmdir(path)
            except (FileNotFoundError, OSError):
                # Deletion might fail if the directory contains ignored files,
                # so it's OK
                pass


def read_tree(tree_oid: str) -> None:
    _empty_current_directory()
    for path, oid in get_tree(tree_oid, base_path="./").items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data.get_object(oid))


def commit(message: str):
    _commit = f"tree {write_tree()}\n"

    HEAD = data.get_ref('HEAD')
    if HEAD:
        _commit += f"parent {HEAD}\n"

    _commit += "\n"
    _commit += f"{message}\n"

    oid = data.hash_object(_commit.encode(), "commit")

    data.update_ref('HEAD', oid)

    return oid


def checkout(oid: str):
    _commit = get_commit(oid)
    read_tree(_commit.tree)
    data.update_ref('HEAD', oid)


def create_tag(name: str, oid: str):
    data.update_ref(f'/refs/tags/{name}', oid)


Commit = namedtuple("Commit", ["tree", "parent", "message"])


def get_commit(oid: str) -> "Commit":
    parent = None

    _commit = data.get_object(oid, "commit").decode()
    lines = iter(_commit.splitlines())
    for line in itertools.takewhile(operator.truth, lines):
        key, value = line.split(" ", 1)
        if key == "tree":
            tree = value
        elif key == "parent":
            parent = value
        else:
            assert False, f"Unknown field {key}"

    message = "\n".join(lines)
    return Commit(tree=tree, parent=parent, message=message)


def is_ignored(path: str) -> bool:
    return ".ugit" in path.split("/")
