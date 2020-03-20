import hashlib

BUFFER_SIZE = 8000000  # 1 MB


def hash_file(path):
    """
    Hashes the file using its first megabyte

    :param path: Full path of the file
    :type path: String
    :return: Hashed value in hexadecimal format
    :rtype: String
    """
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        data = f.read(BUFFER_SIZE)
        md5.update(data)
    return md5.hexdigest()
