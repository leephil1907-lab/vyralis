import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.app.main import validate_source_url


class SourceURLValidationTests(unittest.TestCase):
    def test_rejects_non_https_source(self):
        with self.assertRaises(HTTPException) as error:
            validate_source_url("http://youtube.com/watch?v=abc")
        self.assertEqual(error.exception.status_code, 422)

    def test_rejects_unapproved_host(self):
        with self.assertRaises(HTTPException) as error:
            validate_source_url("https://example.com/video.mp4")
        self.assertEqual(error.exception.status_code, 422)

    def test_rejects_private_or_local_dns_results(self):
        with patch("backend.app.main.socket.getaddrinfo", return_value=[
            (2, 1, 6, "", ("127.0.0.1", 443))
        ]):
            with self.assertRaises(HTTPException) as error:
                validate_source_url("https://youtube.com/watch?v=abc")
        self.assertEqual(error.exception.status_code, 422)

    def test_accepts_allowed_public_provider_host(self):
        with patch("backend.app.main.socket.getaddrinfo", return_value=[
            (2, 1, 6, "", ("93.184.216.34", 443))
        ]):
            result = validate_source_url("https://youtube.com/watch?v=abc")
        self.assertEqual(result, "https://youtube.com/watch?v=abc")


if __name__ == "__main__":
    unittest.main()
