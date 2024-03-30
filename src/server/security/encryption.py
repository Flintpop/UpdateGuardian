import hashlib


class Hasher:
    @staticmethod
    def sha256(file: str) -> str:
        """
        Calculates the sha256 hash of a file.
        :param file: The path of the file to hash.
        :return: The sha256 hash of the file.
        """
        hasher = hashlib.sha256()
        with open(file, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
