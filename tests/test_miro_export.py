import pytest
import responses
import requests
import os
import time
from miro_export import (
    make_miro_request,
    create_export_job,
    get_job_status,
    get_export_results,
    download_file,
    main,
)


@pytest.fixture
def mock_api():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def valid_args(tmp_path):
    return [
        "-t",
        "test_token",
        "-g",
        "org_123",
        "-b",
        "board1",
        "board2",
        "-o",
        str(tmp_path),
    ]


def test_make_miro_request_success(mock_api):
    mock_api.add(
        responses.GET, "https://api.miro.com/test", json={"data": "success"}, status=200
    )
    result = make_miro_request("GET", "https://api.miro.com/test", "token")
    assert result == {"data": "success"}


@pytest.mark.parametrize(
    "status,code",
    [
        (400, "invalidParameters"),
        (401, "unauthorized"),
        (403, "forbiddenAccess"),
        (404, "notFound"),
        (429, "tooManyRequests"),
    ],
)
def test_make_miro_request_errors(mock_api, status, code):
    mock_api.add(
        responses.GET,
        "https://api.miro.com/test",
        json={"status": status, "code": code},
        status=status,
    )
    with pytest.raises(SystemExit) as exc:
        make_miro_request("GET", "https://api.miro.com/test", "token")
    assert exc.value.code == 1


def test_create_export_job(mock_api):
    mock_api.add(
        responses.POST,
        "https://api.miro.com/v2/orgs/org_123/boards/export/jobs",
        json={"jobId": "test_job"},
        status=200,
    )
    create_export_job("token", "org_123", ["board1"], "PDF")

    # Verify query parameters instead of request body
    request_params = mock_api.calls[0].request.params
    assert "request_id" in request_params
    assert isinstance(request_params["request_id"], str)
    assert len(request_params["request_id"]) == 36  # UUID validation


def test_job_status_polling(mock_api):
    # Mock status endpoint responses
    mock_api.add(
        responses.GET,
        "https://api.miro.com/v2/orgs/org_123/boards/export/jobs/test_job",
        json={"jobStatus": "CREATED"},
        status=200,
    )

    mock_api.add(
        responses.GET,
        "https://api.miro.com/v2/orgs/org_123/boards/export/jobs/test_job",
        json={"jobStatus": "IN_PROGRESS"},
        status=200,
    )
    mock_api.add(
        responses.GET,
        "https://api.miro.com/v2/orgs/org_123/boards/export/jobs/test_job",
        json={"jobStatus": "FINISHED"},
        status=200,
    )

    status = get_job_status("token", "org_123", "test_job")
    assert status["jobStatus"] == "CREATED"

    status = get_job_status("token", "org_123", "test_job")
    assert status["jobStatus"] == "IN_PROGRESS"

    status = get_job_status("token", "org_123", "test_job")
    assert status["jobStatus"] == "FINISHED"


def test_export_results(mock_api):
    mock_api.add(
        responses.GET,
        "https://api.miro.com/v2/orgs/org_123/boards/export/jobs/test_job/results",
        json={
            "results": [
                {
                    "boardId": "board1",
                    "exportLink": "http://test.link/file.zip",
                    "status": "SUCCESS",
                }
            ]
        },
        status=200,
    )
    results = get_export_results("token", "org_123", "test_job")
    assert len(results["results"]) == 1


def test_download_file_success(mock_api, tmp_path):
    mock_api.add(
        responses.GET, "http://test.link/file.zip", body=b"test_content", status=200
    )
    output = tmp_path / "test.zip"
    assert download_file("http://test.link/file.zip", output)
    assert os.path.exists(output)


def test_download_file_failure(mock_api):
    mock_api.add(
        responses.GET,
        "http://test.link/file.zip",
        body=requests.exceptions.RequestException(),
    )
    assert not download_file("http://test.link/file.zip", "/invalid/path.zip")


def test_full_workflow(mock_api, valid_args, tmp_path, monkeypatch):
    # Mock API endpoints
    mock_api.add(
        responses.POST,
        "https://api.miro.com/v2/orgs/org_123/boards/export/jobs",
        json={"jobId": "test_job"},
        status=200,
    )
    # Sequence of status responses
    mock_api.add(
        responses.GET,
        "https://api.miro.com/v2/orgs/org_123/boards/export/jobs/test_job",
        json={"jobStatus": "IN_PROGRESS"},
        status=200,
    )
    mock_api.add(
        responses.GET,
        "https://api.miro.com/v2/orgs/org_123/boards/export/jobs/test_job",
        json={"jobStatus": "FINISHED"},
        status=200,
    )
    mock_api.add(
        responses.GET,
        "https://api.miro.com/v2/orgs/org_123/boards/export/jobs/test_job/results",
        json={
            "results": [
                {
                    "boardId": "board1",
                    "exportLink": "http://test.link/file.zip",
                    "status": "SUCCESS",
                }
            ]
        },
        status=200,
    )
    mock_api.add(
        responses.GET, "http://test.link/file.zip", body=b"test_content", status=200
    )

    # Mock sleep to avoid real delays
    def mock_sleep(seconds):
        pass  # Bypass actual waiting

    monkeypatch.setattr(time, "sleep", mock_sleep)

    # Run main with arguments
    with pytest.raises(SystemExit) as exc:
        main(
            [
                "-t",
                "test_token",
                "-g",
                "org_123",
                "-b",
                "board1",
                "board2",
                "-o",
                str(tmp_path),
            ]
        )
    assert exc.value.code == 0
    assert os.path.exists(tmp_path / "board1.zip")


def test_partial_success(mock_api, valid_args, tmp_path):
    mock_api.add(
        responses.POST,
        "https://api.miro.com/v2/orgs/org_123/boards/export/jobs",
        json={"jobId": "test_job"},
        status=200,
    )
    mock_api.add(
        responses.GET,
        "https://api.miro.com/v2/orgs/org_123/boards/export/jobs/test_job",
        json={"jobStatus": "FINISHED"},
        status=200,
    )
    mock_api.add(
        responses.GET,
        "https://api.miro.com/v2/orgs/org_123/boards/export/jobs/test_job/results",
        json={
            "results": [
                {
                    "boardId": "board1",
                    "exportLink": "http://test.link/file.zip",
                    "status": "SUCCESS",
                },
                {
                    "boardId": "board2",
                    "status": "FAILED",
                    "errorMessage": "Export error",
                },
            ]
        },
        status=200,
    )
    mock_api.add(
        responses.GET, "http://test.link/file.zip", body=b"test_content", status=200
    )

    with pytest.raises(SystemExit) as exc:
        main(valid_args)

    assert exc.value.code == 0
    assert os.path.exists(tmp_path / "board1.zip")
    assert not os.path.exists(tmp_path / "board2.zip")
