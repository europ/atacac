import glob

import click
import yamale

from atacac._utils import log
from atacac import validators


@click.command()
@click.option('-v', '--validators', 'custom_validators', multiple=True,
              help='Python scripts with additional validators')
@click.argument('assets_glob', envvar='ASSETS_GLOB')
@click.argument('assets_schema', envvar='ASSETS_SCHEMA', required=False)
def main(assets_glob, assets_schema, custom_validators):
    """
    Validate assets files.
    \f
    Validates the assets with rules defined in the schema.

    !! ASSETS_GLOB must be in single quotes to prevent glob pattern expansion in
    shell.

    \b
    Folloving arguments can be passed via environment variables:
        * ASSETS_GLOB
        * ASSETS_SCHEMA
    """
    # Run only if schema is set
    if assets_schema:
        schema = yamale.make_schema(assets_schema,
                                    validators=validators.load(custom_validators))

        for f in sorted(glob.glob(assets_glob, recursive=True)):
            log('INFO', f"Validating {f} against schema {assets_schema}")
            yamale.validate(schema, yamale.make_data(f))

        log('INFO', "... finished")


if __name__ == '__main__':
    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    main()
