import os
import shutil
import tempfile
from unittest import mock
from test.utils import MockDir

import pytest
from click import Abort
from click.testing import CliRunner

from atacac import restore


@pytest.mark.parametrize(
    "ARTIFACTS_JOB",
    [
        pytest.param(None, id="default artifacts_job"),
        pytest.param("custom_artifacts_job", id="custom artifacts_job"),
    ]
)
@mock.patch("atacac.restore.os")
@mock.patch("atacac.restore.upload")
@mock.patch("atacac.restore.extract")
@mock.patch("atacac.restore.gitlab_download")
def test_main(mock_gitlab_download, mock_extract, mock_upload, mock_os, ARTIFACTS_JOB):
    GITLAB_URL = "VALUE_gitlab_url"
    GITLAB_TOKEN = "VALUE_gitlab_token"
    GITLAB_PROJECT = "VALUE_gitlab_project"

    os.environ["GITLAB_URL"] = GITLAB_URL
    os.environ["GITLAB_TOKEN"] = GITLAB_TOKEN
    os.environ["GITLAB_PROJECT"] = GITLAB_PROJECT

    if ARTIFACTS_JOB:
        os.environ["ARTIFACTS_JOB"] = ARTIFACTS_JOB

    mock_os.path.join.side_effect = os.path.join
    mock_os.getcwd.return_value = "fakeCWD"

    runner = CliRunner()
    result = runner.invoke(restore.main, ["pipeline_id"])

    assert result.output == ""
    assert result.exit_code == 0
    assert result.exception is None

    mock_gitlab_download.assert_called_once()
    mock_gitlab_download.assert_called_with(
        GITLAB_URL,
        GITLAB_TOKEN,
        GITLAB_PROJECT,
        ARTIFACTS_JOB if ARTIFACTS_JOB else "backup",
        "pipeline_id",
        "fakeCWD/artifacts.zip"
    )

    mock_extract.assert_called_once()
    mock_extract.assert_called_with("fakeCWD/artifacts.zip", "fakeCWD/artifacts")

    mock_upload.assert_called_once()
    mock_upload.assert_called_with("fakeCWD/artifacts")


@pytest.mark.parametrize(
    "pipeline_status, jop_status, artifact_job, artifact_name",
    [
        pytest.param("success", "success", "backup", "artifacts.zip", id="default"),
        pytest.param("success", "success", "custom", "artifacts.zip", id="custom"),
        pytest.param("abcdefg", "success", "backup", "artifacts.zip", id="pipeline status != 'success'"),
        pytest.param("success", "abcdefg", "backup", "artifacts.zip", id="job status != 'success'"),
        pytest.param("success", "success", "backup", "abcdefghijklm", id="artifact name != 'artifacts.zip'"),
    ]
)
@mock.patch("atacac.restore.log")
@mock.patch("atacac.restore.gitlab")
def test_gitlab_download(mock_gitlab, mock_log, pipeline_status, jop_status, artifact_job, artifact_name):
    def log_call(*args, **kwargs):
        try:
            if kwargs['fatal']:
                raise Abort
            else:
                pass
        except KeyError:
            pass

    mock_log.side_effect = log_call

    gl = mock_gitlab.Gitlab.return_value
    project = mock.MagicMock()
    pipeline = mock.MagicMock()
    job = mock.MagicMock()
    job_content = mock.MagicMock()

    gl.projects.get.return_value = project

    project.pipelines.get.return_value = pipeline
    project.jobs.get.return_value = job_content

    pipeline.id = 12345
    pipeline.attributes = {
        "status": pipeline_status,
        "sha": "value_sha",
        "web_url": "value_web_url"
    }
    pipeline.jobs.list.return_value = [job]

    job.name = artifact_job
    job.attributes = {
        "status": jop_status,
        "web_url": "value_web_url"
    }
    job.artifacts = [
        {
            "filename": artifact_name,
            "file_format": "value_file_format",
            "size": "value_size"
        }
    ]

    with tempfile.NamedTemporaryFile() as file:
        try:
            restore.gitlab_download(
                "VALUE_url",
                "VALUE_token",
                "VALUE_project",
                artifact_job,
                "VALUE_pipeline_id",
                file.name
            )
        except Abort:
            assert (pipeline_status != "success"
                    or jop_status != "success"
                    or artifact_name != "artifacts.zip")
        else:
            assert mock_log.call_args_list[-1].args[1] == "Successfully downloaded"
            assert [
                call.args[0] for call in mock_log.call_args_list
            ] == ["INFO", "INFO", "INFO", "WARNING", "INFO", "INFO"]


@pytest.mark.parametrize(
    "dir_exists",
    [
        pytest.param(True, id="destination is an existing directory"),
        pytest.param(False, id="destination is an non-existing directory"),
    ]
)
@mock.patch("atacac.restore.log")
def test_extract(mock_log, dir_exists):
    mock_dir = MockDir()
    mock_dir.add_file(["A.yml", "X.yml", "B.yml", "Y.yml"])

    dest_dir = mock_dir.path

    shutil.make_archive("/tmp/atacac_test_archive", "zip", dest_dir)

    if not dir_exists:
        mock_dir.__del__()

    restore.extract("/tmp/atacac_test_archive.zip", dest_dir)

    assert sorted(os.listdir(dest_dir)) == sorted(["A.yml", "X.yml", "B.yml", "Y.yml"])
    assert mock_log.call_count == 3 if dir_exists else 2


@pytest.mark.parametrize(
    "files",
    [
        pytest.param(
            ["A.yml", "X.yml", "B.yml", "Y.yml"],
            id="*.yml files"
        ),
        pytest.param(
            ["A.yaml", "X.yaml", "B.yaml", "Y.yaml"],
            id="*.yaml files (unsupported)"
        ),
        pytest.param(
            ["A.xyz", "X.xyz", "B.xyz", "Y.xyz"],
            id="*.xyz files (unsupported)"
        ),
    ]
)
@mock.patch("atacac.restore.log")
@mock.patch("atacac.restore.tower_send")
def test_upload(mock_tower_send, mock_log, files):
    mock_dir = MockDir()
    mock_dir.add_file(files)

    restore.upload(mock_dir.path)

    yml_files = [file for file in files if file.endswith(".yml")]

    assert [
        call.args[0] for call in mock_log.call_args_list
    ] == [
        "INFO" for _ in range(len(yml_files) + 1)
    ]

    assert sorted([
        str(call.args[0]) for call in mock_tower_send.call_args_list
    ]) == sorted([
        os.path.join(mock_dir.path, file) for file in yml_files
    ])
