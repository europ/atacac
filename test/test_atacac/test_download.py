from unittest import mock

from click.testing import CliRunner

from atacac import download


@mock.patch("atacac.download.open", new_callable=mock.mock_open)
@mock.patch("atacac.download.tower_receive")
@mock.patch("atacac.download.tower_list_all")
def test_main(mock_tower_list_all, mock_tower_receive, mock_open):
    mock_tower_list_all.return_value = [
        {'id': 1, 'type': 'project', 'name': 'Example project'},
        {'id': 2, 'type': 'inventory', 'name': 'Example inventory'},
        {'id': 3, 'type': 'job_template', 'name': 'Example job_template'},
    ]

    def tower_receive(asset_type, asset_name):
        return [{'asset_type': asset_type, 'name': asset_name}]

    mock_tower_receive.side_effect = tower_receive

    runner = CliRunner()
    result = runner.invoke(download.main, ['1', 'assets'])

    assert result.exit_code == 0
    assert result.exception is None

    mock_tower_list_all.assert_called_with([('labels', '1')])

    mock_tower_receive.assert_has_calls([
        mock.call('project', 'Example project'),
        mock.call('inventory', 'Example inventory'),
        mock.call('job_template', 'Example job_template'),
    ])

    mock_open.assert_has_calls([
        # Example project
        mock.call('assets/Example_project.project.yml', 'w'),
        mock.call().__enter__(),
        mock.call().write('---\n'),
        mock.call().write('asset_type: project\nname: Example project\n'),
        mock.call().__exit__(None, None, None),
        # Example inventory
        mock.call('assets/Example_inventory.inventory.yml', 'w'),
        mock.call().__enter__(),
        mock.call().write('---\n'),
        mock.call().write('asset_type: inventory\nname: Example inventory\n'),
        mock.call().__exit__(None, None, None),
        # Example job_template
        mock.call('assets/Example_job_template.job_template.yml', 'w'),
        mock.call().__enter__(),
        mock.call().write('---\n'),
        mock.call().write('asset_type: job_template\nname: Example job_template\n'),
        mock.call().__exit__(None, None, None)
    ])
