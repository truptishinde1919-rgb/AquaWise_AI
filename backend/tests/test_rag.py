from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys

import httpx
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app import rag


def test_metadata_does_not_invent_optional_publication_details():
    metadata = rag.ResearchMetadata.from_dict({"title": "Verified title"})
    assert metadata.title == "Verified title"
    assert metadata.authors is None
    assert metadata.publication_year is None
    assert metadata.doi is None


def test_metadata_rejects_missing_title():
    with pytest.raises(ValueError, match="title"):
        rag.ResearchMetadata.from_dict({})


def test_metadata_rejects_non_web_source_url():
    with pytest.raises(ValueError, match="HTTP or HTTPS"):
        rag.ResearchMetadata.from_dict({"title": "Verified title", "source_url": "javascript:alert(1)"})


def test_cc_by_4_license_is_permitted_with_attribution_metadata():
    metadata = rag.ResearchMetadata.from_dict(
        {
            "title": "Verified paper",
            "authors": ["A. Author"],
            "publication_year": 2016,
            "source_url": "https://doi.org/10.0000/example",
            "doi": "10.0000/example",
            "license": "CC BY 4.0",
        }
    )
    rag.ensure_ingestion_permitted(metadata)


@pytest.mark.parametrize(
    "license_value",
    ["CC BY-NC-ND 4.0", "CC BY-NC 4.0", None, "All rights reserved"],
)
def test_restricted_or_unspecified_license_is_not_permitted(license_value):
    metadata = rag.ResearchMetadata.from_dict(
        {
            "title": "Restricted paper",
            "authors": ["A. Author"],
            "publication_year": 2024,
            "source_url": "https://example.org/paper",
            "license": license_value,
        }
    )
    with pytest.raises(rag.LicenseNotPermittedError, match="CC BY 4.0"):
        rag.ensure_ingestion_permitted(metadata)


def test_permitted_license_still_requires_attribution_details():
    metadata = rag.ResearchMetadata.from_dict(
        {
            "title": "Paper",
            "license": "CC BY 4.0",
        }
    )
    with pytest.raises(ValueError, match="verified authors"):
        rag.ensure_ingestion_permitted(metadata)


def test_chunking_preserves_page_numbers_and_limits_chunk_size():
    pages = [(4, "First paragraph with evidence.\n\n" + ("agriculture " * 300)), (8, "Second page.")]
    chunks = rag.chunk_pages(pages, max_chars=250, overlap_chars=20)
    assert chunks
    assert all(len(chunk["text"]) <= 250 for chunk in chunks)
    assert {chunk["page_number"] for chunk in chunks} == {4, 8}


def test_chunking_rejects_invalid_size():
    with pytest.raises(ValueError, match="Chunk sizes"):
        rag.chunk_pages([(1, "text")], max_chars=100, overlap_chars=100)


def test_chunking_keeps_overlap_and_never_exceeds_limit():
    chunks = rag.chunk_pages([(2, "paragraph " * 400)], max_chars=200, overlap_chars=40)
    assert len(chunks) > 1
    assert all(len(chunk["text"]) <= 200 for chunk in chunks)
    assert chunks[0]["text"][-20:] in chunks[1]["text"]


def test_extract_pdf_pages_rejects_non_pdf_path(tmp_path):
    text_file = tmp_path / "paper.txt"
    text_file.write_text("not a PDF", encoding="utf-8")
    with pytest.raises(ValueError, match="PDF"):
        rag.extract_pdf_pages(text_file)


def test_extract_pdf_pages_rejects_empty_pdf(tmp_path):
    fitz = pytest.importorskip("pymupdf")
    pdf_path = tmp_path / "empty.pdf"
    document = fitz.open()
    document.new_page()
    document.save(pdf_path)
    with pytest.raises(ValueError, match="no extractable text"):
        rag.extract_pdf_pages(pdf_path)


def test_extract_pdf_pages_keeps_source_page_numbers(tmp_path):
    fitz = pytest.importorskip("pymupdf")
    pdf_path = tmp_path / "paper.pdf"
    document = fitz.open()
    document.new_page().insert_text((72, 72), "First page evidence.")
    document.new_page().insert_text((72, 72), "Second page evidence.")
    document.save(pdf_path)
    pages = rag.extract_pdf_pages(pdf_path)
    assert pages == [(1, "First page evidence."), (2, "Second page evidence.")]


def test_bundled_frontiers_paper_citations_match_actual_pdf_pages():
    pdf_path = BACKEND_DIR / "data" / "research" / "papers" / "frontiers-2016-plant-disease.pdf"
    pages = dict(rag.extract_pdf_pages(pdf_path))
    chunks = rag.chunk_pages(list(pages.items()))
    assert "54,306" in pages[1]
    assert "99.35" in pages[1]
    assert "PlantVillage" in pages[2]
    assert "31%" in pages[8]
    for page_number, claim in ((1, "99.35"), (2, "PlantVillage"), (8, "31%")):
        assert any(
            chunk["page_number"] == page_number and claim in chunk["text"]
            for chunk in chunks
        )


def test_embedding_generation_accepts_ordered_vectors(monkeypatch):
    monkeypatch.setattr(rag, "_api_key", lambda: "test-key")

    async def fake_post(endpoint, payload, **kwargs):
        assert endpoint == "embeddings"
        assert payload["model"] == rag.EMBEDDING_MODEL
        vector = [0.1] * rag.EMBEDDING_DIMENSIONS
        return {
            "data": [
                {"index": 1, "embedding": vector},
                {"index": 0, "embedding": vector},
            ]
        }

    monkeypatch.setattr(rag, "_openai_post", fake_post)
    vectors = asyncio.run(rag.generate_embeddings(["first", "second"]))
    assert len(vectors) == 2
    assert len(vectors[0]) == rag.EMBEDDING_DIMENSIONS


def test_embedding_rejects_empty_text():
    with pytest.raises(ValueError, match="non-empty"):
        asyncio.run(rag.generate_embeddings([""]))


def test_embedding_rejects_malformed_vector(monkeypatch):
    async def fake_post(endpoint, payload):
        return {"data": [{"index": 0, "embedding": [float("nan")] * rag.EMBEDDING_DIMENSIONS}]}

    monkeypatch.setattr(rag, "_openai_post", fake_post)
    with pytest.raises(rag.RagServiceError, match="invalid vectors"):
        asyncio.run(rag.generate_embeddings(["text"]))


def test_vector_search_returns_page_cited_provenance_and_logs_ids(caplog, monkeypatch):
    caplog.set_level("INFO", logger=rag.__name__)
    row = (
        41,
        73,
        "Irrigation research",
        ["A. Author"],
        2022,
        "https://example.org/paper",
        "10.0000/example",
        "CC BY 4.0",
        6,
        "Evidence about irrigation water.",
        0.88,
    )

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def execute(self, query, params):
            assert "SELECT d.id, c.id" in query
            assert "ORDER BY c.embedding <=> %s" in query
            assert params[-1] == 5
            return self

        def fetchall(self):
            return [row]

    chunks = rag.search_research_chunks(
        [0.0] * rag.EMBEDDING_DIMENSIONS,
        connection_factory=FakeConnection,
    )
    citation = rag.citation_for_chunk(chunks[0])
    assert citation["title"] == "Irrigation research"
    assert citation["page_number"] == 6
    assert citation["source_url"] == "https://example.org/paper"
    assert citation["doi"] == "10.0000/example"
    assert chunks[0]["document_id"] == 41
    assert chunks[0]["chunk_id"] == 73
    assert "document_id=41 chunk_id=73 page_number=6 similarity=0.8800" in caplog.text


def test_vector_search_filters_low_similarity(monkeypatch):
    row = (1, 2, "title", None, None, None, None, None, 1, "text", 0.1)

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def execute(self, *args):
            return self

        def fetchall(self):
            return [row]

    monkeypatch.setenv("RAG_MIN_SIMILARITY", "0.2")
    assert rag.search_research_chunks(
        [0.0] * rag.EMBEDDING_DIMENSIONS,
        connection_factory=FakeConnection,
    ) == []


def test_vector_search_fails_clearly_when_database_has_no_chunks(monkeypatch):
    monkeypatch.delenv("RAG_MIN_SIMILARITY", raising=False)

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def execute(self, query, params=None):
            class Result:
                @staticmethod
                def fetchall():
                    return []

                @staticmethod
                def fetchone():
                    return (0,)

            return Result()

    with pytest.raises(rag.RagServiceError, match="collection is empty"):
        rag.search_research_chunks(
            [0.0] * rag.EMBEDDING_DIMENSIONS,
            connection_factory=FakeConnection,
        )


def test_vector_search_rejects_invalid_similarity_setting(monkeypatch):
    monkeypatch.setenv("RAG_MIN_SIMILARITY", "1.5")
    with pytest.raises(rag.RagServiceError, match="between 0 and 1"):
        rag.search_research_chunks([0.0] * rag.EMBEDDING_DIMENSIONS)


def test_prompt_cites_evidence_and_blocks_chemical_instructions():
    prompt = rag.build_rag_prompt(
        "How to manage a crop disease?",
        [{"title": "Paper", "page_number": 3, "text": "Retrieved evidence"}],
    )
    assert "[1]" in prompt[1]["content"]
    assert "Do not give pesticide doses" in prompt[0]["content"]
    assert "evidence_sufficient" in prompt[0]["content"]
    assert "not AquaWise AI's model accuracy" in prompt[0]["content"]


def test_prompt_includes_recent_chat_history():
    prompt = rag.build_rag_prompt(
        "Follow-up",
        [{"title": "Paper", "page_number": 3, "text": "Retrieved evidence"}],
        [{"role": "user", "content": "Earlier question"}],
    )
    assert prompt[1]["content"] == "Earlier question"


def test_generate_answer_returns_real_provider_response(monkeypatch):
    async def fake_post(endpoint, payload):
        assert endpoint == "chat/completions"
        assert payload["response_format"] == {"type": "json_object"}
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"answer":"Evidence-based answer [1].","evidence_sufficient":true}'
                    }
                }
            ]
        }

    monkeypatch.setattr(rag, "_openai_post", fake_post)
    answer = asyncio.run(
        rag.generate_answer("Question", [{"title": "Paper", "page_number": 2, "text": "Evidence"}])
    )
    assert answer == rag.RagAnswer("Evidence-based answer [1].", True, (1,))


def test_generate_answer_abstains_when_retrieved_excerpt_does_not_answer(monkeypatch):
    async def fake_post(endpoint, payload):
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"answer":"The retrieved paper does not establish a pesticide '
                            'recommendation.","evidence_sufficient":false}'
                        )
                    }
                }
            ]
        }

    monkeypatch.setattr(rag, "_openai_post", fake_post)
    result = asyncio.run(
        rag.generate_answer(
            "What is the best pesticide?",
            [{"title": "Plant disease paper", "page_number": 2, "text": "CNN image classification."}],
        )
    )
    assert result.evidence_sufficient is False
    assert "does not establish" in result.answer


def test_generate_answer_rejects_accuracy_without_paper_attribution(monkeypatch):
    async def fake_post(endpoint, payload):
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"answer":"The model achieved 99.35% accuracy [1].",'
                            '"evidence_sufficient":true}'
                        )
                    }
                }
            ]
        }

    monkeypatch.setattr(rag, "_openai_post", fake_post)
    with pytest.raises(rag.RagServiceError, match="performance figure"):
        asyncio.run(
            rag.generate_answer(
                "What accuracy did it achieve?",
                [{"title": "Paper", "page_number": 1, "text": "Reported accuracy: 99.35%."}],
            )
        )


def test_generate_answer_accepts_explicitly_attributed_paper_accuracy(monkeypatch):
    answer_text = (
        "The study reported 99.35% held-out accuracy; this is the paper's result, "
        "not AquaWise AI's model accuracy [1]."
    )

    async def fake_post(endpoint, payload):
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {"answer": answer_text, "evidence_sufficient": True}
                        )
                    }
                }
            ]
        }

    monkeypatch.setattr(rag, "_openai_post", fake_post)
    result = asyncio.run(
        rag.generate_answer(
            "What accuracy did it achieve?",
            [{"title": "Paper", "page_number": 1, "text": "Reported accuracy: 99.35%."}],
        )
    )
    assert result.answer == answer_text


def test_generate_answer_rejects_citation_outside_retrieved_sources(monkeypatch):
    async def fake_post(endpoint, payload):
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"answer":"Unsupported citation [7].","evidence_sufficient":true}'
                    }
                }
            ]
        }

    monkeypatch.setattr(rag, "_openai_post", fake_post)
    with pytest.raises(rag.RagServiceError, match="invalid source citation"):
        asyncio.run(
            rag.generate_answer("Question", [{"title": "Paper", "page_number": 2, "text": "Evidence"}])
        )


def test_malformed_llm_response_is_an_explicit_provider_error(monkeypatch):
    async def fake_post(endpoint, payload):
        return {"choices": []}

    monkeypatch.setattr(rag, "_openai_post", fake_post)
    with pytest.raises(rag.RagServiceError, match="malformed data"):
        asyncio.run(
            rag.generate_answer("Question", [{"title": "Paper", "page_number": 2, "text": "Evidence"}])
        )


@pytest.mark.parametrize(
    ("status_code", "expected_status", "expected_text"),
    [
        (401, 503, "credentials"),
        (429, 429, "rate-limiting"),
        (503, 502, "unavailable"),
    ],
)
def test_openai_provider_errors_are_explicit(
    monkeypatch, status_code, expected_status, expected_text
):
    monkeypatch.setattr(rag, "_api_key", lambda: "test-key")
    calls = 0

    class FakeResponse:
        def __init__(self, status):
            self.status_code = status
            self.headers = {}
            self.is_success = 200 <= status < 300

        def json(self):
            return {}

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            return False

        async def post(self, *args, **kwargs):
            nonlocal calls
            calls += 1
            return FakeResponse(status_code)

    with pytest.raises(rag.RagServiceError) as error:
        asyncio.run(
            rag._openai_post(
                "chat/completions",
                {},
                client_factory=FakeClient,
            )
        )
    assert error.value.status_code == expected_status
    assert expected_text in str(error.value)
    assert calls <= rag.MAX_RETRIES + 1


def test_openai_timeout_maps_to_gateway_timeout(monkeypatch):
    monkeypatch.setattr(rag, "_api_key", lambda: "test-key")

    class TimeoutClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            return False

        async def post(self, *args, **kwargs):
            raise httpx.TimeoutException("timeout")

    with pytest.raises(rag.RagServiceError) as error:
        asyncio.run(rag._openai_post("chat/completions", {}, client_factory=TimeoutClient))
    assert error.value.status_code == 504


def test_missing_api_key_is_not_silently_ignored(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(rag.RagServiceError, match="OPENAI_API_KEY"):
        rag._api_key()


def test_missing_database_url_is_reported_without_connection_details(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(rag.RagServiceError, match="DATABASE_URL is missing"):
        rag.connect_database()
    status = rag.rag_database_status()
    assert status == {
        "status": "unconfigured",
        "database_configured": False,
        "database_connected": False,
        "pgvector_available": False,
        "schema_available": False,
        "document_count": None,
        "chunk_count": None,
    }


def test_database_status_reports_ready_counts_without_credentials(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@db.example/private")

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def execute(self, query):
            class Result:
                def fetchone(self):
                    if query == "SELECT 1":
                        return (1,)
                    if "pg_extension" in query:
                        return (True, True, True)
                    return (1, 3)

            return Result()

    monkeypatch.setattr(
        rag,
        "connect_database",
        lambda **kwargs: FakeConnection(),
    )
    status = rag.rag_database_status()
    assert status == {
        "status": "ready",
        "database_configured": True,
        "database_connected": True,
        "pgvector_available": True,
        "schema_available": True,
        "document_count": 1,
        "chunk_count": 3,
    }
    assert "password" not in str(status)
    assert "db.example" not in str(status)


def test_database_status_distinguishes_empty_research_collection(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def execute(self, query):
            class Result:
                def fetchone(self):
                    if query == "SELECT 1":
                        return (1,)
                    if "pg_extension" in query:
                        return (True, True, True)
                    return (0, 0)

            return Result()

    monkeypatch.setattr(rag, "connect_database", lambda **kwargs: FakeConnection())
    assert rag.rag_database_status()["status"] == "empty"


def test_database_status_sanitizes_unavailable_database(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:secret@db.example/private")

    def unavailable(**kwargs):
        raise rag.RagServiceError("database unavailable")

    monkeypatch.setattr(rag, "connect_database", unavailable)
    status = rag.rag_database_status()
    assert status["status"] == "unavailable"
    assert status["database_configured"] is True
    assert "secret" not in str(status)
    assert "db.example" not in str(status)


def test_database_status_logs_presence_flags_without_values(caplog, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://diagnostic-user:private-value@db.example/secret-db")
    monkeypatch.setenv("OPENAI_API_KEY", "diagnostic-openai-secret")
    monkeypatch.setattr(
        rag,
        "connect_database",
        lambda **kwargs: (_ for _ in ()).throw(rag.RagServiceError("unavailable")),
    )
    with caplog.at_level("INFO", logger=rag.__name__):
        rag.rag_database_status()
    assert "database_url_present=True openai_api_key_present=True" in caplog.text
    for secret in ("private-value", "db.example", "secret-db", "diagnostic-openai-secret"):
        assert secret not in caplog.text


def test_database_connect_logs_driver_type_without_connection_details(caplog, monkeypatch):
    import sys
    import types

    class FakeDatabaseError(Exception):
        sqlstate = "08001"

    def fail_connect(_database_url):
        raise FakeDatabaseError("sensitive connection detail")

    fake_psycopg = types.ModuleType("psycopg")
    fake_psycopg.Error = FakeDatabaseError
    fake_psycopg.connect = fail_connect
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)
    monkeypatch.setenv("DATABASE_URL", "postgresql://private-user:private-password@private-host/private-db")
    with caplog.at_level("ERROR", logger=rag.__name__), pytest.raises(
        rag.RagServiceError,
        match="database is unavailable",
    ):
        rag.connect_database(register_vector_type=False)
    assert "reason=Other connection error error_type=FakeDatabaseError sqlstate=08001" in caplog.text
    assert "detail=No recognized connection failure signature." in caplog.text
    for secret in ("private-password", "private-host", "private-db"):
        assert secret not in caplog.text


@pytest.mark.parametrize(
    ("raw_message", "expected_reason"),
    [
        ("[Errno 11001] getaddrinfo failed for secret.host", "DNS resolution failure"),
        ("connection timed out for host=secret.host", "Connection timeout"),
        ("connection refused at 10.1.2.3:6543", "Connection refused"),
        ("password authentication failed for user secret-user", "Authentication failure"),
        ("invalid port 6543 for host=secret.host", "Invalid hostname or port"),
        ("SSL negotiation failed for postgresql://secret:password@secret.host/db", "SSL negotiation failure"),
        ("unexpected driver failure secret-token", "Other connection error"),
    ],
)
def test_database_error_classification_is_secret_safe(
    raw_message, expected_reason, monkeypatch
):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://secret:password@secret.host:6543/db?sslmode=require",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "secret-openai-key")
    error = RuntimeError(raw_message)
    assert rag._classify_database_error(error) == expected_reason
    safe_detail = rag._safe_database_error_message(error)
    assert safe_detail == rag._DATABASE_ERROR_DETAILS[expected_reason]
    for secret in (
        "secret.host", "secret-user", "password", "secret-token",
        "10.1.2.3", "6543", "secret-openai-key",
    ):
        assert secret not in safe_detail


def test_database_status_runs_select_one_and_logs_sanitized_query_errors(caplog, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://private-user:private-password@private-host:6543/private-db")
    monkeypatch.setenv("OPENAI_API_KEY", "diagnostic-openai-secret")

    class FakeDatabaseError(Exception):
        sqlstate = "42501"

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def execute(self, query):
            assert query == "SELECT 1"
            raise FakeDatabaseError(
                "could not connect to postgresql://private-user:private-password@private-host:6543/private-db "
                "host=private-host port=6543; sensitive query detail diagnostic-openai-secret"
            )

    monkeypatch.setattr(rag, "connect_database", lambda **kwargs: FakeConnection())
    with caplog.at_level("ERROR", logger=rag.__name__):
        status = rag.rag_database_status()

    assert status["status"] == "unavailable"
    assert status["database_connected"] is False
    assert (
        "stage=connectivity_check reason=Other connection error "
        "error_type=FakeDatabaseError sqlstate=42501" in caplog.text
    )
    assert "sensitive query detail" not in caplog.text
    assert "detail=No recognized connection failure signature." in caplog.text
    assert "diagnostic-openai-secret" not in caplog.text
    assert "private-user" not in caplog.text
    assert "private-password" not in caplog.text
    assert "private-host" not in caplog.text
    assert "6543" not in caplog.text


def test_provider_request_uses_backend_bearer_auth(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-key")

    class FakeResponse:
        status_code = 200
        is_success = True

        @staticmethod
        def json():
            return {"ok": True}

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] == rag.REQUEST_TIMEOUT_SECONDS

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            return False

        async def post(self, url, headers, json):
            assert url == f"{rag.OPENAI_API_URL}/chat/completions"
            assert headers["Authorization"] == "Bearer unit-test-key"
            assert json == {"messages": []}
            return FakeResponse()

    result = asyncio.run(
        rag._openai_post(
            "chat/completions",
            {"messages": []},
            client_factory=FakeClient,
        )
    )
    assert result == {"ok": True}


def test_ingestion_rejects_duplicate_document(tmp_path, monkeypatch):
    fitz = pytest.importorskip("pymupdf")
    pdf_path = tmp_path / "paper.pdf"
    document = fitz.open()
    document.new_page().insert_text((72, 72), "Research evidence.")
    document.save(pdf_path)

    class FakeTransaction:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

    class FakeConnection:
        def transaction(self):
            return FakeTransaction()

        def execute(self, query, params):
            class Result:
                @staticmethod
                def fetchone():
                    return (1,)

            return Result()

    with pytest.raises(rag.DuplicateDocumentError):
        rag.ingest_pdf(
            pdf_path,
            rag.ResearchMetadata.from_dict(
                {
                    "title": "Verified",
                    "authors": ["A. Author"],
                    "publication_year": 2024,
                    "source_url": "https://example.org/paper",
                    "license": "CC BY 4.0",
                }
            ),
            [[0.0] * rag.EMBEDDING_DIMENSIONS],
            FakeConnection(),
        )


def test_duplicate_is_detected_before_embedding_work(tmp_path):
    pdf_path = tmp_path / "duplicate.pdf"
    pdf_path.write_bytes(b"PDF bytes")

    class FakeConnection:
        def execute(self, query, params):
            assert params[0] == rag.document_sha256(pdf_path)

            class Result:
                @staticmethod
                def fetchone():
                    return (1,)

            return Result()

    with pytest.raises(rag.DuplicateDocumentError):
        rag.ensure_new_pdf(pdf_path, FakeConnection())


def test_ingestion_stores_document_and_page_chunks(tmp_path):
    fitz = pytest.importorskip("pymupdf")
    pdf_path = tmp_path / "paper.pdf"
    document = fitz.open()
    document.new_page().insert_text((72, 72), "First page research evidence.")
    document.new_page().insert_text((72, 72), "Second page research evidence.")
    document.save(pdf_path)
    statements = []

    class FakeTransaction:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

    class FakeConnection:
        def transaction(self):
            return FakeTransaction()

        def execute(self, query, params):
            statements.append((query, params))

            class Result:
                @staticmethod
                def fetchone():
                    if "SELECT id FROM research_documents" in query:
                        return None
                    if "RETURNING id" in query:
                        return (27,)
                    return None

            return Result()

    count = rag.ingest_pdf(
        pdf_path,
        rag.ResearchMetadata.from_dict(
            {
                "title": "Verified paper",
                "authors": ["A. Author"],
                "publication_year": 2024,
                "source_url": "https://example.org/paper",
                "license": "CC BY 4.0",
            }
        ),
        [[0.0] * rag.EMBEDDING_DIMENSIONS, [0.1] * rag.EMBEDDING_DIMENSIONS],
        FakeConnection(),
    )
    assert count == 2
    document_insert = next(
        params for query, params in statements if "INSERT INTO research_documents" in query
    )
    assert document_insert[1:7] == (
        "Verified paper",
        ["A. Author"],
        2024,
        "https://example.org/paper",
        None,
        "CC BY 4.0",
    )
    chunks = [params for query, params in statements if "INSERT INTO research_chunks" in query]
    assert [chunk[1] for chunk in chunks] == [1, 2]
    assert [chunk[0] for chunk in chunks] == [27, 27]
    assert [chunk[2] for chunk in chunks] == [
        "First page research evidence.",
        "Second page research evidence.",
    ]
    assert all(chunk[3].dimensions() == rag.EMBEDDING_DIMENSIONS for chunk in chunks)


def test_schema_matches_vector_search_columns_and_embedding_dimensions():
    schema = (BACKEND_DIR / "sql" / "rag_schema.sql").read_text(encoding="utf-8")
    assert "research_documents" in schema
    assert "research_chunks" in schema
    assert "sha256 CHAR(64) NOT NULL UNIQUE" in schema
    assert "embedding vector(1536) NOT NULL" in schema
    assert "vector_cosine_ops" in schema
    assert rag.EMBEDDING_DIMENSIONS == 1536
