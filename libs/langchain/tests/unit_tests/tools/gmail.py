import json
from typing import Any, Dict, List

import pytest
from googleapiclient.errors import HttpError

from langchain.langchain.tools.gmail.search import GmailSearch, Resource


class MockMessages:
    def __init__(self, messages: List[Dict[str, Any]]):
        self.messages = messages

    def list(self, **kwargs):
        return self

    def execute(self):
        return {"messages": self.messages}


class MockThreads:
    def __init__(self, threads: List[Dict[str, Any]]):
        self.threads = threads

    def list(self, **kwargs):
        return self

    def execute(self):
        return {"threads": self.threads}


class MockUsers:
    def __init__(self, messages: List[Dict[str, Any]], threads: List[Dict[str, Any]]):
        self.messages = MockMessages(messages)
        self.threads = MockThreads(threads)

    def messages(self):
        return self.messages

    def threads(self):
        return self.threads


class MockGmailApiResource:
    def __init__(self, messages: List[Dict[str, Any]], threads: List[Dict[str, Any]]):
        self.users = lambda: MockUsers(messages, threads)


class TestGmailSearch:
    def test_run_messages(self, mocker):
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
            "langchain.langchain.tools.gmail.search.build",
            return_value=MockGmailApiResource(messages, []),
        )
        search = GmailSearch()
        results = search.run(query="test", resource=Resource.MESSAGES, max_results=2)
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[0]["threadId"] == "1"
        assert results[0]["snippet"] == "Test message 1"
        assert results[1]["id"] == "2"
        assert results[1]["threadId"] == "2"
        assert results[1]["snippet"] == "Test message 2"

    def test_run_threads(self, mocker):
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
            "langchain.langchain.tools.gmail.search.build",
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
        mocker.patch(
            "langchain.langchain.tools.gmail.search.build",
            return_value=MockGmailApiResource([], []),
        )
        search = GmailSearch()
        with pytest.raises(NotImplementedError):
            search.run(query="test", resource="invalid_resource", max_results=2)

    def test_run_http_error(self, mocker):
        mocker.patch(
            "langchain.langchain.tools.gmail.search.build",
            side_effect=HttpError(
                resp={"status": 404, "reason": "Not Found"}, content=b"Not Found"
            ),
        )
        search = GmailSearch()
        with pytest.raises(HttpError):
            search.run(query="test", resource=Resource.MESSAGES, max_results=2)

    def test_parse_messages(self):
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
        results = search._parse_messages(messages)
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[0]["threadId"] == "1"
        assert results[0]["snippet"] == "Test message 1"
        assert results[1]["id"] == "2"
        assert results[1]["threadId"] == "2"
        assert results[1]["snippet"] == "Test message 2"

    def test_parse_threads(self):
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
        results = search._parse_threads(threads)
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[0]["snippet"] == "Test thread 1"
        assert results[1]["id"] == "2"
        assert results[1]["snippet"] == "Test thread 2"
