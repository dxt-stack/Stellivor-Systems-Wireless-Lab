import socket
import unittest
from unittest.mock import patch

from stellivor.core import PlatformInfo, Status
from stellivor.network import check_tcp, interface_information, resolve_dns, route_information, validate_hostname


class HostValidationTests(unittest.TestCase):
    def test_valid_hosts(self):
        self.assertEqual(validate_hostname(" Example.COM "), "example.com")
        self.assertEqual(validate_hostname("127.0.0.1"), "127.0.0.1")
        self.assertEqual(validate_hostname("[::1]"), "::1")
        self.assertEqual(validate_hostname("localhost"), "localhost")

    def test_invalid_hosts(self):
        for value in ("", "https://example.com", "example.com/path", "example.com:80", "bad host", "-bad.example", "user@example.com"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_hostname(value)


class NetworkTests(unittest.TestCase):
    @patch("stellivor.network.socket.getaddrinfo")
    def test_dns_deduplicates_addresses(self, mocked):
        mocked.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.1", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.1", 0)),
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2001:db8::1", 0, 0, 0)),
        ]
        result = resolve_dns("example.com")
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertEqual(len(result.data["addresses"]), 2)
        mocked.assert_called_once()

    @patch("stellivor.network.socket.getaddrinfo", side_effect=socket.gaierror("test failure"))
    def test_dns_error_is_failure(self, _mocked):
        result = resolve_dns("example.com")
        self.assertEqual(result.status, Status.FAILURE)
        self.assertFalse(result.data["resolved"])

    def test_invalid_port_does_not_attempt_connection(self):
        result = check_tcp("localhost", 0)
        self.assertEqual(result.status, Status.FAILURE)
        self.assertEqual(result.data["connection_attempts"], 0)

    @patch("stellivor.network.socket.socket")
    @patch("stellivor.network._getaddrinfo")
    def test_one_successful_tcp_attempt(self, resolver, socket_factory):
        resolver.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]
        connection = socket_factory.return_value
        connection.getsockname.return_value = ("127.0.0.1", 50000)
        result = check_tcp("localhost", 80)
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertEqual(result.data["connection_attempts"], 1)
        connection.connect.assert_called_once_with(("127.0.0.1", 80))
        connection.close.assert_called_once()

    @patch("stellivor.network.socket.socket")
    @patch("stellivor.network._getaddrinfo")
    def test_failed_tcp_attempt_is_failure(self, resolver, socket_factory):
        resolver.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]
        socket_factory.return_value.connect.side_effect=ConnectionRefusedError("refused")
        result = check_tcp("localhost", 80)
        self.assertEqual(result.status, Status.FAILURE)
        self.assertFalse(result.data["connected"])
        socket_factory.return_value.close.assert_called_once()

    def test_unknown_platform_adapters_are_unsupported(self):
        info = PlatformInfo("unknown", "Plan9")
        self.assertEqual(interface_information(info).status, Status.UNSUPPORTED)
        self.assertEqual(route_information(info).status, Status.UNSUPPORTED)


if __name__ == "__main__":
    unittest.main()
