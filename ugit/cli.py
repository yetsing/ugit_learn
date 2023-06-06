import argparse
import os
import subprocess
import sys
import textwrap

from . import base, data


def main():
    args = parse_args()
    args.func(args)


def parse_args():
    parser = argparse.ArgumentParser()

    commands = parser.add_subparsers(dest="command")
    commands.required = True

    oid = base.get_oid

    init_parser = commands.add_parser("init")
    # parse_args 方法会返回一个对象
    # set_defaults 可以设置这个对象的一些属性
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser("hash-object")
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument("file")

    cat_file_parser = commands.add_parser("cat-file")
    cat_file_parser.set_defaults(func=cat_file)
    # type - The type to which the command-line argument should be converted.
    cat_file_parser.add_argument("object", type=oid)

    write_tree_parser = commands.add_parser("write-tree")
    write_tree_parser.set_defaults(func=write_tree)

    read_tree_parser = commands.add_parser("read-tree")
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument("tree", type=oid)

    commit_parser = commands.add_parser("commit")
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument("-m", "--message", required=True)

    log_parser = commands.add_parser("log")
    log_parser.set_defaults(func=log)
    log_parser.add_argument("oid", default="@", type=oid, nargs="?")

    checkout_parser = commands.add_parser("checkout")
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument("commit")

    tag_parser = commands.add_parser("tag")
    tag_parser.set_defaults(func=tag)
    tag_parser.add_argument("name")
    tag_parser.add_argument("oid", default="@", type=oid, nargs="?")

    branch_parser = commands.add_parser("branch")
    branch_parser.set_defaults(func=branch)
    branch_parser.add_argument("name", nargs="?")
    branch_parser.add_argument("start_point", default="@", type=oid, nargs="?")

    k_parser = commands.add_parser("k")
    k_parser.set_defaults(func=k)

    status_parser = commands.add_parser('status')
    status_parser.set_defaults(func=status)

    reset_parser = commands.add_parser('reset')
    reset_parser.set_defaults(func=reset)
    reset_parser.add_argument('commit', type=oid)

    return parser.parse_args()


def init(args: argparse.Namespace):
    base.init()
    print(f"Initialized empty ugit repository in {os.getcwd()}/{data.GIT_DIR}")


def hash_object(args: argparse.Namespace):
    with open(args.file, "rb") as f:
        print(data.hash_object(f.read()))


def cat_file(args: argparse.Namespace):
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected=None))


def write_tree(args: argparse.Namespace):
    print(base.write_tree())


def read_tree(args: argparse.Namespace):
    base.read_tree(args.tree)


def commit(args: argparse.Namespace):
    print(base.commit(args.message))


def log(args: argparse.Namespace):
    refs = {}
    for refname, ref in data.iter_refs():
        refs.setdefault(ref.value, []).append(refname)

    for oid in base.iter_commits_and_parents({args.oid}):
        _commit = base.get_commit(oid)

        refs_str = f' ({", ".join(refs[oid])})' if oid in refs else ''
        print(f'commit {oid}{refs_str}\n')
        print(textwrap.indent(_commit.message, "    "))
        print("")


def checkout(args: argparse.Namespace):
    base.checkout(args.commit)


def tag(args: argparse.Namespace):
    base.create_tag(args.name, args.oid)


def branch(args: argparse.Namespace):
    if not args.name:
        current = base.get_branch_name()
        for _branch in base.iter_branch_names():
            prefix = '*' if _branch == current else ' '
            print(f'{prefix} {_branch}')
    else:
        base.create_branch(args.name, args.start_point)
        print(f"Branch {args.name} created at {args.start_point[:10]}")


def k(args: argparse.Namespace):
    dot = "digraph commits {\n"

    oids = set()
    for refname, ref in data.iter_refs(deref=False):
        dot += f'"{refname}" [shape=note]\n'
        dot += f'"{refname}" -> "{ref.value}"\n'
        if not ref.symbolic:
            oids.add(ref.value)

    for oid in base.iter_commits_and_parents(oids):
        _commit = base.get_commit(oid)
        dot += f'"{oid}" [shape=box style=filled label="{oid[:10]}"]\n'
        if _commit.parent:
            dot += f'"{oid}" -> "{_commit.parent}"\n'

    dot += "}"
    print(dot)

    with subprocess.Popen(
            ["dot", "-Tx11", "/dev/stdin"], stdin=subprocess.PIPE
    ) as proc:
        proc.communicate(dot.encode())


def status(args: argparse.Namespace) -> None:
    HEAD = base.get_oid('@')
    _branch = base.get_branch_name()
    if _branch:
        print(f'On branch {_branch}')
    else:
        print(f'HEAD detached at {HEAD[:10]}')


def reset(args: argparse.Namespace) -> None:
    base.reset(args.commit)
