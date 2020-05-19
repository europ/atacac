import os
import shutil
import zipfile
import pathlib

import gitlab
import click

from atacac._utils import log, tower_send


@click.command()
@click.option('--gitlab-url', envvar='GITLAB_URL')
@click.option('--gitlab-token', envvar='GITLAB_TOKEN')
@click.option('--gitlab-project', envvar='GITLAB_PROJECT')
@click.option('--artifacts-job', envvar='ARTIFACTS_JOB', default='backup')
@click.argument('pipeline_id')
def main(gitlab_url, gitlab_token, gitlab_project, artifacts_job, pipeline_id):
    # downloaded archive file path (artifacts.zip)
    dest_file_path = os.path.join(os.getcwd(), 'artifacts.zip')

    # extracted archive destination directory path
    dest_dir_path = os.path.join(os.getcwd(), 'artifacts')

    gitlab_download(
        gitlab_url,
        gitlab_token,
        gitlab_project,
        artifacts_job,
        pipeline_id,
        dest_file_path
    )

    extract(dest_file_path, dest_dir_path)

    upload(dest_dir_path)


def gitlab_download(url, token, project, artifacts_job, pipeline_id, file_path):
    gl = gitlab.Gitlab(url, token)
    gl.auth()
    project = gl.projects.get(project)
    pipeline = project.pipelines.get(pipeline_id)

    log('INFO', (f"Pipeline: {pipeline.id}\n"
                 f"  Status: {pipeline.attributes['status']}\n"
                 f"  Commit: {pipeline.attributes['sha']}\n"
                 f"  URL: {pipeline.attributes['web_url']}"))

    if pipeline.attributes['status'] != 'success':
        log('ERROR', "Pipeline's status is not 'success'!", fatal=True)

    job_backup = next(job for job in pipeline.jobs.list()
                      if job.name == artifacts_job)

    log('INFO', (f"  Job: {artifacts_job}\n"
                 f"    Status: {job_backup.attributes['status']}\n"
                 f"    URL: {job_backup.attributes['web_url']}"))

    if job_backup.attributes['status'] != 'success':
        log('ERROR', "Job's status is not 'success'!", fatal=True)

    for artifact in job_backup.artifacts:
        if artifact['filename'] == 'artifacts.zip':
            log('INFO', (f"    Artifact: {artifact['filename']}\n"
                         f"      Format: {artifact['file_format']}\n"
                         f"      Size: {artifact['size']}"))
            break
    else:
        log('ERROR', "Invalid artifact!", fatal=True)

    try:
        if os.path.isfile(file_path):
            log('WARNING', f"Rewriting file: '{file_path}'")
        with open(file_path, "wb") as f:
            project.jobs.get(job_backup.id).artifacts(streamed=True, action=f.write)
    except EnvironmentError:
        log('ERROR', f"Failed to write to the file! Path: {file_path}", fatal=True)

    log('INFO', "File path (artifacts - archive): '{file_path}'")
    log('INFO', "Successfully downloaded")


def extract(src_archive, dest_dir):
    if os.path.isdir(dest_dir):
        log('WARNING', f"Rewriting directory: '{dest_dir}'")

    shutil.rmtree(dest_dir, ignore_errors=True)

    with zipfile.ZipFile(src_archive, 'r') as zf:
        zf.extractall(dest_dir)

    log('INFO', f"Directory path (artifacts - extracted): '{dest_dir}'")
    log('INFO', "Successfully extracted")


def upload(src_dir):
    for path in pathlib.Path(src_dir).rglob('*.yml'):
        asset_name = os.path.basename(  # noqa: F841 (variable never used)
            os.path.splitext(path.name)[0].replace('_', ' '))
        log('INFO', f"Sending '{asset_name}' from '{path}'")
        tower_send(path)

    log('INFO', "Successfully sent")


if __name__ == "__main__":
    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    main()
