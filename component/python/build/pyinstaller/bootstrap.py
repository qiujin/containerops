#!/usr/bin/env python3

import subprocess
import os
import sys
import glob

REPO_PATH = 'git-repo'


def git_clone(url):
    r = subprocess.run(['git', 'clone', url, REPO_PATH])

    if r.returncode == 0:
        return True
    else:
        print("[COUT] Git clone error: Invalid argument to exit",
              file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return False


def get_pip_cmd(version):
    if version == 'py3k' or version == 'python3':
        return 'pip3'

    return 'pip'


def get_python_cmd(version):
    if version == 'py3k' or version == 'python3':
        return 'python3'

    return 'python'


def init_env(version):
    subprocess.run([get_pip_cmd(version), 'install', 'pyinstaller'])


def validate_version(version):
    valid_version = ['python', 'python2', 'python3', 'py3k']
    if version not in valid_version:
        print("[COUT] Check version failed: the valid version is {}".format(valid_version), file=sys.stderr)
        return False

    return True


def setup(path, version='py3k'):
    file_name = os.path.basename(path)
    dir_name = os.path.dirname(path)
    r = subprocess.run('cd {}; {} {} install'.format(dir_name, get_python_cmd(version), file_name),
                       shell=True)

    if r.returncode != 0:
        print("[COUT] install dependences failed", file=sys.stderr)
        return False

    return True


def pip_install(file_name, version='py3k'):
    r = subprocess.run([get_pip_cmd(version), 'install', '-r', file_name])

    if r.returncode != 0:
        print("[COUT] install dependences failed", file=sys.stderr)
        return False

    return True


def upload_file(upload):
    parsed = upload.split('/')
    host = parsed[0]
    namespace = parsed[1]
    repo = parsed[2]
    binary = parsed[3]
    tag = parsed[4]
    url = 'https://{}/binary/v1/{}/{}/binary/{}/{}'.format(host, namespace,
                                                           repo, binary, tag)

    r1 = subprocess.run(['curl', '-XPUT', '-d', '@/tmp/output.tar.bz2', url])
    if r1.returncode != 0:
        print("[COUT] upload error", file=sys.stderr)
        return False
    print()
    return True


def pyinstaller(file_name):
    r = subprocess.run(['pyinstaller', '{}/{}'.format(REPO_PATH, file_name)])

    if r.returncode != 0:
        print("[COUT] pyinstaller error", file=sys.stderr)
        return False

    return True


def compress():
    r = subprocess.run('cd dist; tar cjvf /tmp/output.tar.bz2 .', shell=True)

    if r.returncode != 0:
        print("[COUT] compress error", file=sys.stderr)
        return False

    return True


def parse_argument():
    data = os.environ.get('CO_DATA', None)
    if not data:
        return {}

    validate = ['git-url', 'entry-file', 'upload', 'version']
    ret = {}
    for s in data.split(' '):
        s = s.strip()
        if not s:
            continue
        arg = s.split('=')
        if len(arg) < 2:
            print('[COUT] Unknown Parameter: [{}]'.format(s))
            continue

        if arg[0] not in validate:
            print('[COUT] Unknown Parameter: [{}]'.format(s))
            continue

        ret[arg[0]] = arg[1]

    return ret


def main():
    argv = parse_argument()
    git_url = argv.get('git-url')
    if not git_url:
        print("[COUT] The git-url value is null", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return

    version = argv.get('version', 'py3k')

    if not validate_version(version):
        print("[COUT] CO_RESULT = false")
        return

    init_env(version)

    entry_file = argv.get('entry-file')
    if not entry_file:
        print("[COUT] The entry-file value is null", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return

    upload = argv.get('upload')
    if not upload:
        print("[COUT] The upload value is null", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return

    if not git_clone(git_url):
        return

    for file_name in glob.glob('{}/setup.py'.format(REPO_PATH)):
        setup(file_name, version)

    for file_name in glob.glob('{}/*/setup.py'.format(REPO_PATH)):
        setup(file_name, version)

    for file_name in glob.glob('{}/requirements.txt'.format(REPO_PATH)):
        pip_install(file_name, version)

    for file_name in glob.glob('{}/*/requirements.txt'.format(REPO_PATH)):
        pip_install(file_name, version)

    if not pyinstaller(entry_file):
        print("[COUT] CO_RESULT = false")
        return

    if not compress():
        print("[COUT] CO_RESULT = false")
        return

    if not upload_file(upload):
        print("[COUT] CO_RESULT = false")
        return

    print("[COUT] CO_RESULT = true")


main()
