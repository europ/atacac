# Example

**This is example how repository can look like.**

## Files

* `.gitlab-ci.yml` -- GitLab CI configuration file. Copied
  [.TEMPLATE.gitlab-ci.yml] and changed `LABEL_ID`, `ASSETS_GLOB` and
  `ASSETS_SCHEMA` in `variables` section.
* `.yamllint` -- Example yamllint configuration used to check assets files and
  other yaml files if any.
* `assets/` -- Directory with all Ansible Tower Assets.
* `schemas/` -- Custom yamale schemas to validate assets.
* `validators/` -- Directory with custom validators. Python scripts that declare
  custom yamale validators.
* `validators/config/` -- Config directory for custom validators, if you want to
  separate validators code and configuration for them.

[.TEMPLATE.gitlab-ci.yml]: ../.TEMPLATE.gitlab-ci.yml
