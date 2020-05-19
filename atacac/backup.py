import os

import yaml
import click

from atacac._utils import log, tower_list, tower_receive


class Dumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(Dumper, self).increase_indent(flow, False)


@click.command()
@click.argument('label_id', envvar='LABEL_ID')
@click.argument('destination', envvar='BACKUP_PATH')
def main(label_id, destination):
    try:
        os.makedirs(destination, exist_ok=True)
    except OSError:
        log('ERROR', f"Directory path: {destination}")
        log('ERROR', "Failed to create directory!", fatal=True)

    job_templates_3SN = tower_list('job_template', [('labels', label_id)])

    for jt in job_templates_3SN:
        jt_name = jt['name']
        log('INFO', f"Downloading '{jt_name}' ...")
        jt_file = os.path.join(destination, jt_name.replace(' ', '_') + '.yml')
        jt_data = tower_receive('job_template', jt_name)[0]
        content = yaml.dump(jt_data, Dumper=Dumper, default_flow_style=False)

        try:
            log('INFO', f"    File path: {jt_file}")
            with open(jt_file, 'w') as file:
                file.write("---\n")
                file.write(content)
        except EnvironmentError:
            log('ERROR', "Failed to write to the file!", fatal=True)

        log('INFO', "... downloaded")


if __name__ == "__main__":
    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    main()
