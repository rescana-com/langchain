"""Unit tests for GmailSearch class."""
import pytest

from langchain.tools.gmail.search import GmailSearch, Resource


class MockGmailApiResource:
    """Mock Gmail API resource."""

    def __init__(self, messages, threads):
        self.messages = messages
        self.threads = threads

    def users(self):
        """Mock users method."""
        return self

    def messages(self):
        """Mock messages method."""
        return self

    def threads(self):
        """Mock threads method."""
        return self

    def list(self, userId, q, maxResults):
        """Mock list method."""
        if self.messages:
            return {"messages": self.messages}
        return {"threads": self.threads}


    def test_run_messages(mocker):
        """Test run_messages method."""
        messages = [
            {
                "id": "1",
                "threadId": "1",
                "snippet": "Test message 1",
            },
            {
                "id": "2",
                "threadId": "2",
                "snippet": "Test message 2",
            },
        ]
        mocker.patch(
            "googleapiclient.discovery.build",
            return_value=MockGmailApiResource(messages, []),
        )
        search = GmailSearch()
        results = search.run(query="test", resource=Resource.MESSAGES, max_results=2)
        assert len(results)
        assert results[0]["id"] == "1"
        assert results[0]["threadId"] == "1"
        assert results[0]["snippet"] == "Test message 1"
        assert results[1]["id"] == "2"
        assert results[1]["threadId"] == "2"
        assert results[1]["snippet"] == "Test message 2"
        assert results[0]["body"] == "VGhpcyBpcyBhIHRlc3QgbWVzc2FnZSAx\n"

    def test_run_threads(self, mocker):
        """Test run_threads method."""
        threads = [
            {
                "id": "1",
                "snippet": "Test thread 1",
            },
            {
                "id": "2",
                "snippet": "Test thread 2",
            },
        ]
        mocker.patch(
            "googleapiclient.discovery.build",
            return_value=MockGmailApiResource([], threads),
        )
        search = GmailSearch()
        results = search.run(query="test", resource=Resource.THREADS, max_results=2)
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[0]["snippet"] == "Test thread 1"
        assert results[1]["id"] == "2"
        assert results[1]["snippet"] == "Test thread 2"

    def test_run_invalid_resource(self, mocker):
        """Test run_invalid_resource method."""
        mocker.patch(
            "googleapiclient.discovery.build",
            return_value=MockGmailApiResource([], []),
        )
        search = GmailSearch()
        with pytest.raises(NotImplementedError):
            search.run(query="test", resource="invalid_resource", max_results=2)


    def test_parse_messages(self):
        """Test parse_messages method."""
        messages = [
            {
                "id": "1",
                "threadId": "1",
                "snippet": "Test message 1",
            },
            {
                "id": "2",
                "threadId": "2",
                "snippet": "Test message 2",
            },
        ]
        search = GmailSearch()
        results = search._GmailSearch__parse_messages(messages)
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[0]["threadId"] == "1"
        assert results[0]["snippet"] == "Test message 1"
        assert results[1]["id"] == "2"
        assert results[1]["threadId"] == "2"
        assert results[1]["snippet"] == "Test message 2"
        assert results[0]["body"] == "VGhpcyBpcyBhIHRlc3QgbWVzc2FnZSAx\n"

    def test_parse_threads(self):
        """Test parse_threads method."""
        threads = [
            {
                "id": "1",
                "snippet": "Test thread 1",
            },
            {
                "id": "2",
                "snippet": "Test thread 2",
            },
        ]
        search = GmailSearch()
        results = search._GmailSearch__parse_threads(threads)
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[0]["snippet"] == "Test thread 1"
        assert results[1]["id"] == "2"
        assert results[1]["snippet"] == "Test thread 2"

    def test_parse_messages_with_encoding(self):
        """Test parse_messages_with_encoding method."""
        messages = [
            {
                "id": "1",
                "threadId": "1",
                "snippet": "Test message 1",
                "payload": {
                    "headers": [
                        {
                            "name": "Content-Type",
                            "value": "text/plain; charset=iso-8859-1",
                        }
                    ],
                    "body": {
                        "data": "VGhpcyBpcyBhIHRlc3QgbWVzc2FnZSAx",
                        "size": 24,
                    },
                },
            },
            {
                "id": "2",
                "threadId": "2",
                "snippet": "Test message 2",
                "payload": {
                    "headers": [
                        {
                            "name": "Content-Type",
                            "value": "text/plain; charset=utf-8",
                        }
                    ],
                    "body": {
                        "data": "VGhpcyBpcyBhIHRlc3QgbWVzc2FnZSAy",
                        "size": 24,
                    },
                },
            },
        ]
        search = GmailSearch()
        results = search._GmailSearch__parse_messages(messages)
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[0]["threadId"] == "1"
        assert results[0]["snippet"] == "Test message 1"
        assert results[0]["body"] == "This is a test message 1"
        assert results[1]["id"] == "2"
        assert results[1]["threadId"] == "2"
        assert results[1]["snippet"] == "Test message 2"
        assert results[1]["body"] == "This is a test message 2"

    def test_parse_messages_with_invalid_encoding(self):
        """Test parse_messages_with_invalid_encoding method."""
        messages = [
            {
                "id": "1",
                "threadId": "1",
                "snippet": "Test message 1",
                "payload": {
                    "headers": [
                        {
                            "name": "Content-Type",
                            "value": "text/plain; charset=invalid_encoding",
                        }
                    ],
                    "body": {
                        "data": "VGhpcyBpcyBhIHRlc3QgbWVzc2FnZSAx",
                        "size": 24,
                    },
                },
            },
        ]
        search = GmailSearch()
        results = search._GmailSearch__parse_messages(messages)
        assert len(results) == 1
        assert results[0]["id"] == "1"
        assert results[0]["threadId"] == "1"
        assert results[0]["snippet"] == "Test message 1"
        assert results[0]["body"] == "VGhpcyBpcyBhIHRlc3QgbWVzc2FnZSAx\n"
