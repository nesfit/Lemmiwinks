import hashlib

def hash_file(filename):
    sha = hashlib.sha256()
    with open(filename, "rb") as fd:
        while True:
            data = fd.read(4096)
            if not data:
                break
            sha.update(data)
    return str(sha.hexdigest())
