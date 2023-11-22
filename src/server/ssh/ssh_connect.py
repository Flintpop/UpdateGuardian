import paramiko
import chardet

from src.server.Exceptions.DecodingExceptions import DecodingError


def decode_stream(stream) -> str | None:
    """
    Decode a stream.
    :param stream: The stream to decode.
    :return: The decoded stream.
    """
    if stream is None or stream == b'':
        return None

    encodings = ['cp850', chardet.detect(stream)['encoding'], 'cp1252', 'iso-8859-1', 'utf-8', 'utf-16', 'utf-32']

    for encoding in encodings:
        try:
            return stream.decode(encoding, errors="replace").strip().replace("\r\n", "\n").replace("\r", "")
        except UnicodeDecodeError:
            pass

    raise DecodingError("None of the tested encodings were able to decode the stream")
