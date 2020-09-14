# Documentation

## Introduction

The project was designed to work from GitLab CI, however all the steps in the workflow are wrapped
in a standalone script or container, so you can use your own CI/CD framework to define the individual steps.

You can have a look at our example [.gitlab-ci.yml](../example/.gitlab-ci.yml).

Continue further for instructions specific to GitLab.

## Table of Contents

1. [Setup](#setup)
    1. [Prerequisites](#prerequisites)
    1. [Configuration](#configuration)
        1. [Remote](#remote)
        1. [Local](#local)
    1. [Usage](#usage)
1. [Workflow](#workflow)
    1. [Sequence Diagrams](#sequence-diagrams)
        1. [Change Request](#change-request)
        1. [Restore Backup](#restore-backup)
1. [Example Structure](#example-structure)
1. [Example Pipeline](#example-pipeline)
1. [FAQ](#frequently-asked-questions)
    1. [Why tower cli?](#why-tower-cli)
    1. [Why are labels important?](#why-are-labels-important)
    1. [Will ATACAC delete Tower assets?](#will-atacac-delete-tower-assets)
    1. [Why is the pipeline failing on 'differentiation' but still continuing?](#why-is-the-pipeline-failing-on-differentiation-but-still-continuing)
1. [Future Work](#future-work)
1. [Notes](#notes)

## Setup

### Prerequisites

1. GitLab environment
    1. Domain
        * e.g. `https://your.gitlab.domain.com/`
    1. Repository
        * e.g. `owner/repository`
    1. Account
        * has all the necessary permissions to the repository
        * personal access token, e.g. `efgh5678`
            * `api` scope
1. Ansible Tower
    1. Ansible Tower server
        * URL of the host, e.g. `https://your.tower.domain.com/`
    1. Ansible Tower account with sufficient permissions for read and modify
        * username, e.g. `towerbot`
        * password, e.g. `abcd1234`
1. ATACAC installed
    1. [python3](https://www.python.org/)
    1. python3 [pip](https://github.com/pypa/pip)
    1. `pip3 install --user atacac`

### Configuration

#### Remote

1. Create new project
    1. create new project GitLab as you are used to do
    1. download `.TEMPLATE.gitlab-ci.yml` and add it to your project
1. Go to your project repository
1. Enable GitLab runner for the project
    1. Open `CI/CD` settings
    1. Expand `Runners` section
    1. Add specific runners or use shared runners
1. Add environment variables to the project
    * `TOWER_HOST`, `TOWER_USERNAME` and `TOWER_PASSWORD`
    * `TOWER_CERTIFICATE` if you are using custom CA or self-signed
      certificates, value should be path to certificate or you can use
      [variable of type
      File](https://docs.gitlab.com/ee/ci/variables/#custom-environment-variables-of-type-file)
1. Add assets (YAML files) to the repository (folder, eg. `data/assets/`)
    * You can download the already existing ones with `atacac download <LABEL_ID> data/assets`
1. Configure the validation schema stored in `data/schemas/`
    * You can check asset validating schema locally via `atacac validate 'data/assets/*_<type>.yml' 'data/schemas/<type>.yml'`
    * This step is optional. If you don't need additional assurance that assets are correct you can skip this and remove `validation` job from the pipeline.
1. Rename `.TEMPLATE.gitlab-ci.yml` to `.gitlab-ci.yml`
1. Fill in placeholders in `.gitlab-ci.yml`, they are marked with `<TODO>`
    * Find the placeholder(s) via `grep -nF '<TODO>' .gitlab-ci.yml` and replace them
    * To find the corresponding ID to the label run `tower-cli label list -a`
1. Rename `TEMPLATE.README.md` to `README.md`
    * Add valid values to the placeholders

#### Local

1. Configured Ansible Tower CLI
    * <https://tower-cli.readthedocs.io/en/latest/>
    * add `host`, `username` and `password`
        * as environment variables or stored in `~/.tower_cli.cfg`
    * set also `certificate` if you are using custom CA or self-signed
      certificates
1. Configured GitLab API
    * `GITLAB_URL`, `GITLAB_TOKEN` and `GITLAB_PROJECT` (`owner/repository` format)
1. Clone of your forked repository including the desired assets

Variables for shell (you can add it to your `~/.profile`, `~/.bashrc`, direnv, ...):

```sh
export TOWER_HOST=
export TOWER_USERNAME=
export TOWER_PASSWORD=
export TOWER_CERTIFICATE=
export GITLAB_URL=
export GITLAB_TOKEN=
export GITLAB_PROJECT=
```

### Usage

See

```sh
atacac --help
```

#### Docker container

You can also use docker container to run `atacac` command but you'll need to pass all environment variables to container.

```sh
docker run --rm -it \
    -v "$PWD:/workdir:Z" \
    -e "TOWER_HOST=$TOWER_HOST" \
    -e "TOWER_USERNAME=$TOWER_USERNAME" \
    -e "TOWER_PASSWORD=$TOWER_PASSWORD" \
    -e "TOWER_CERTIFICATE=$TOWER_CERTIFICATE" \
    -e "GITLAB_URL=$GITLAB_URL" \
    -e "GITLAB_TOKEN=$GITLAB_TOKEN" \
    -e "GITLAB_PROJECT=$GITLAB_PROJECT" \
    europ/atacac <command> <args...>
```

## Workflow

The repository must include runner, assets in `data/assets/` folder, credentials stored in environment variables, and the required implementation for validation, tower interaction, and further configuration. The pipeline defined in `.gitlabl-ci.yml` is triggered for each change request (such as commit) including the following pipeline stages:

* linting
    * `yamllint`, ...
    * static analysis of the files in the repository
* validating
    * `atacac validate`
    * asset validation based on the [Yamale schema](https://github.com/23andMe/Yamale)
* differentiating
    * `atacac differentiate`
    * asset differentiation between current stored assets and current Ansible Tower assets (defined in `atacac/differentiate.py`)
    * *this command exits with error code if there are differences between stored assets and Tower*
* synchronizing
    * `atacac synchronize`
    * check for new or removed assets tagged with a specific label in the Ansible Tower (defined in `atacac/synchronize.py`)
* backup
    * `atacac backup`
    * download and store the files to the given folder from Ansible Tower (defined in `atacac/backup.py`)
    * downloads only assets that are stored locally - makes backup
* uploading
    * `atacac upload`
    * rewrite the corresponding Ansible Tower assets with repository assets
* downloading
    * `atacac download`
    * download all assets including dependencies with given label
    * downloads all assets - for initial download to the repository

The automated workflow does not restore the backup stored in the job's artifacts. Each pipeline run stores the actual assets located in the Ansible Tower into a [job artifact](https://docs.gitlab.com/ee/ci/pipelines/job_artifacts.html) (in our case called backup) before it will write (upload) anything to the Ansible Tower. This artifact is an archive including the actual assets that are downloaded. If something went wrong, there is a possibility to turn in back by doing a backup restore via [`restore`](ratacac/estore.py), which must be done manually.

The restoration process requires to have a successful backup that is stored as a [job artifact](https://docs.gitlab.com/ee/ci/pipelines/job_artifacts.html) and a pipeline ID that includes the job artifact. The whole process is performed on a developers local machine. It is needed to execute `python3 restore.py <Pipeline ID>`, which will download the artifacts archive, extract the archive, upload the containing files to the Ansible Tower. The interactions inside of the restoration process are shown in sequence diagram below - [Restore Backup](#restore-backup).

### Sequence Diagrams

#### Change Request

![change_request](img/sequence_diagram_1.svg)

#### Restore Backup

![restore_backup](img/sequence_diagram_2.svg)

## Example Structure

```txt
├── assets ................................ ansible tower assets stored in repository
│   ├── <asset_name>.yml .................. 'asset name' asset
│   └── ...
├── schemas ............................... asset validation schemas
│   ├── <asset_name>.schema.yml ........... 'asset name' schema for '<asset_name>.yml'
│   └── ...
├── validators ............................ custom yamale validators
│   ├── custom.py ......................... python source code with validators
│   └── ...
├── .yamllint ............................. yamllint configuration
├── .gitlab-ci.yml ........................ CI configuration
└── ...
```

See also [directory with example repository](../example)

## Example Pipeline

#### Success

![pipeline_success](img/pipeline/pipeline_success.png)

#### Warning

* attribute(s) changed of an existing asset in Ansible Tower

![pipeline_warning](img/pipeline/pipeline_warning.png)

#### Failed (intended)

* completely new asset(s) was(were) added to Ansible Tower which are not available in the repository

![pipeline_failed](img/pipeline/pipeline_failed_intended.png)

#### Failed (unintended)

* an introduced mistake, e.g. broken style guide

![pipeline_failed](img/pipeline/pipeline_failed_unintended.png)

### Validation

#### Success

![success](img/validation/validation_success.png)

#### Error

![error](img/validation/validation_error.png)

## Frequently Asked Questions

### Why tower cli?

1. it does what is needed even it's deprecated
    * dump (list) labeled assets
    * upload (send/import) asset(s)
    * download (receive/export) asset(s)
1. newer cli is not ready yet which is suppose to replace this one
1. it's required functions were wrapped so it is easy to migrate to other (newer) CLI
    * to migrate from `tower-cli` you just need to change few lines in **three** functions located in file `atacac/_utils.py`; `tower_list`, `tower_receive` and `tower_send`.

### Why are labels important?

Labels are how we identify assets in Tower. Labels allow us to specify a category of assets and also to identify when we have extra assets in Tower which don't exist in configuration. One use case is when we want to remove an asset, if we remove it from configuration but not from Tower then the pipeline will fail and let us know.

### Will ATACAC delete Tower assets?

No, by design ATACAC will never delete assets. While deletion may be rolled back, the newly created asset will have a different ID in Tower and this may break some users of templates. Also as a safety reason, we don't want to accidentally delete things. We think there should be a human taking these decisions for now.

### Why is the pipeline failing on 'differentiation' but still continuing?

This step should signify that new assets are added to Tower (they exist in config, but not in Tower yet). For now this is the method we use, we can eventually switch to just a warning.

## Future Work

* add a way to test changes using Stage Tower (pre-merge) when post-merge we apply changes to Prod Tower would require two sets of credentials

## Notes

* `ansible-tower-cli` does not export `verbosity` if it is set to `0`
