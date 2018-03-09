import sys
from mock import patch, mock_open, call, Mock
from pkg_resources import parse_version

from replaceUsingPackageVersion.replace_using_package_version import (
    apply_regex_to_file,
    find_package_version,
    main,
    run_command,
    init
)

from replaceUsingPackageVersion.version import __version__


open_to_patch = '{0}.open'.format(
    sys.version_info.major < 3 and "__builtin__" or "builtins"
)


class TestRegexReplacePackageVersion(object):

    def test_version(self):
        assert __version__ is not None
        assert parse_version(__version__) > parse_version('')

    @patch(open_to_patch, new_callable=mock_open, read_data=(
        'This is a new line\n'
        'this is another new line\n'
        'and yet another line\n'
    ))
    def test_apply_regex_to_file(self, mock_file):
        apply_regex_to_file('input', 'output', 'another', 'CHANGED')
        mock_file.assert_has_calls([call('input', 'r')])
        handler = mock_file()
        handler.write.assert_called_once_with((
            'This is a new line\n'
            'this is CHANGED new line\n'
            'and yet CHANGED line\n'
        ))

    @patch((
        'replaceUsingPackageVersion.'
        'replace_using_package_version.run_command'
    ))
    @patch('os.walk')
    def test_find_package_version(self, mock_walk, mock_run):
        mock_walk.return_value = [
            ('/foo', ['bar', 'zez'], ['baz']),
            ('/foo/bar', [], ['spam', 'package.rpm']),
            ('/foo/zez', [], ['package.rpm', 'somefile'])
        ]
        outputs = ['2.3.1', 'package', '2.2.4', 'package']

        def cmd_output(command):
            return outputs.pop()

        mock_run.side_effect = cmd_output
        assert find_package_version('package', '/foo') == '2.3.1'
        mock_run.assert_has_calls([
            call([
                'rpm', '-qp', '--queryformat',
                '%{NAME}', '/foo/bar/package.rpm'
            ]),
            call([
                'rpm', '-qp', '--queryformat',
                '%{VERSION}', '/foo/bar/package.rpm'
            ]),
        ])

    @patch((
        'replaceUsingPackageVersion.'
        'replace_using_package_version.run_command'
    ))
    @patch('os.walk')
    def test_find_package_version_not_found(self, mock_walk, mock_run):
        mock_walk.return_value = [
            ('/foo', ['bar', 'zez'], ['baz']),
            ('/foo/bar', [], ['spam', 'package.rpm']),
            ('/foo/zez', [], ['package.rpm', 'somefile'])
        ]
        outputs = ['another_non_matching_name', 'not_matching_name']

        def cmd_output(command):
            return outputs.pop()

        mock_run.side_effect = cmd_output
        try:
            find_package_version('package', '/foo') == '2.3.1'
        except Exception as e:
            assert 'Package not found' in str(e)
        mock_run.assert_has_calls([
            call([
                'rpm', '-qp', '--queryformat',
                '%{NAME}', '/foo/bar/package.rpm'
            ]),
            call([
                'rpm', '-qp', '--queryformat',
                '%{NAME}', '/foo/zez/package.rpm'
            ])
        ])

    @patch((
        'replaceUsingPackageVersion.'
        'replace_using_package_version.apply_regex_to_file'
    ))
    @patch((
        'replaceUsingPackageVersion.'
        'replace_using_package_version.find_package_version'
    ))
    @patch('docopt.docopt')
    @patch('os.path.isdir')
    @patch('os.path.isfile')
    def test_main_package(
        self, mock_isfile, mock_isdir, mock_docopt,
        mock_find_pkg, mock_apply_regex
    ):
        mock_isdir.return_value = True
        mock_isfile.return_value = True
        mock_docopt.return_value = {
            '--package': 'package',
            '--file': 'file',
            '--outdir': 'outdir',
            '--regex': 'regex'
        }
        mock_find_pkg.return_value = '0.0.1'
        main()
        mock_find_pkg.assert_called_once_with(
            'package', './repos'
        )
        mock_apply_regex.assert_called_once_with(
            'file', 'outdir/file', 'regex', '0.0.1'
        )

    @patch((
        'replaceUsingPackageVersion.'
        'replace_using_package_version.apply_regex_to_file'
    ))
    @patch('docopt.docopt')
    @patch('os.path.isdir')
    @patch('os.path.isfile')
    def test_main_replacement(
        self, mock_isfile, mock_isdir, mock_docopt, mock_apply_regex
    ):
        mock_isdir.return_value = True
        mock_isfile.return_value = True
        mock_docopt.return_value = {
            '--replacement': 'replacement',
            '--file': 'file',
            '--outdir': 'outdir',
            '--regex': 'regex',
            '--package': None
        }
        main()
        mock_apply_regex.assert_called_once_with(
            'file', 'outdir/file', 'regex', 'replacement'
        )

    @patch('docopt.docopt')
    def test_main_no_file(self, mock_docopt):
        mock_docopt.return_value = {
            '--file': 'file'
        }
        try:
            main()
        except Exception as e:
            assert 'File file not found' in str(e)

    @patch('os.path.isfile')
    @patch('docopt.docopt')
    def test_main_no_outdir(self, mock_docopt, mock_file):
        mock_file.return_value = True
        mock_docopt.return_value = {
            '--file': 'file',
            '--outdir': 'outdir'
        }
        try:
            main()
        except Exception as e:
            assert 'Output directory outdir not found' in str(e)

    @patch('subprocess.Popen')
    def test_run_command(self, mock_subprocess):
        mock_process = Mock()
        mock_process.communicate.return_value = (b'stdout', b'stderr')
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        assert run_command(['/bin/dummycmd', 'arg1']) == 'stdout'

    @patch('subprocess.Popen')
    def test_run_command_failure(self, mock_subprocess):
        mock_process = Mock()
        mock_process.communicate.return_value = (None, None)
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process
        try:
            run_command(['dummycmd', 'arg1']) == 'stdout'
        except Exception as e:
            assert 'Command "dummycmd arg1" failed' in str(e)

    @patch((
        'replaceUsingPackageVersion.'
        'replace_using_package_version.main'
    ))
    def test_main(self, mock_main):
        init('__main__')
        assert mock_main.called
