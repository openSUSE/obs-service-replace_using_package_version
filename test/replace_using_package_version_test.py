import sys
from mock import patch, mock_open, call

from replace_using_package_version.replace_using_package_version import (
    apply_regex_to_file,
    find_package_version,
    find_match_in_version,
    main,
    run_command,
    init,
    version_regex
)

open_to_patch = '{0}.open'.format(
    sys.version_info.major < 3 and "__builtin__" or "builtins"
)


class TestRegexReplacePackageVersion(object):
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

    def test_find_match_in_version(self):
        match = find_match_in_version(version_regex['major'], '0.0.1')
        assert match == '0'
        match = find_match_in_version(
            version_regex['minor'],
            '0.0.1~rev+af232f')
        assert match == '0.0'

        match = find_match_in_version(
            version_regex['patch'],
            '0.0.1~rev+af232f')
        assert match == '0.0.1'
        match = find_match_in_version(
            version_regex['patch'],
            '234~rev+af232f')
        assert match == '234'

        match = find_match_in_version(
            version_regex['minor'], 'as234~rev+af232f')
        assert match == 'as234~rev+af232f'

        match = find_match_in_version(
            version_regex['patch_update'], '234~rev+af232f')
        assert match == '234'
        match = find_match_in_version(
            version_regex['patch_update'],
            '14.2.1.468+g994fd9e0cc')
        assert match == '14.2.1.468'
        match = find_match_in_version(
            version_regex['patch_update'],
            '0.0.1~rev+af232f')
        assert match == '0.0.1'

        match = find_match_in_version(
            version_regex['offset'],
            '3.14.1+git5.g9265358')
        assert match == '5'
        match = find_match_in_version(
            version_regex['offset'],
            '3.14.1+svn592')
        assert match == '592'
        match = find_match_in_version(
            version_regex['offset'],
            '2.14.1+cvs20130621')
        assert match == '20130621'
        match = find_match_in_version(
            version_regex['offset'],
            '0.0.1~rev+af232f')
        assert match == '0.0.1~rev+af232f'
        match = find_match_in_version(
            version_regex['offset'],
            '234~rev+af232f')
        assert match == '234~rev+af232f'
        match = find_match_in_version(
            version_regex['offset'],
            '14.2.1.468+g994fd9e0cc')
        assert match == '14.2.1.468+g994fd9e0cc'

    @patch('subprocess.check_output')
    def test_find_package_version(self, mock_run):
        mock_run.return_value = b'2.3.1'
        assert find_package_version('package', '/foo') == '2.3.1'
        mock_run.called_once_with([
            'rpm', '-q', '--queryformat',
            '%{NAME}', 'package.rpm'
        ])

    @patch('subprocess.check_output')
    @patch('os.walk')
    def test_find_package_version_rpm_not_installed(self, mock_walk, mock_run):
        mock_walk.return_value = [
            ('/foo', ['bar', 'zez'], ['baz']),
            ('/foo/bar', [], ['spam', 'package.rpm']),
            ('/foo/zez', [], ['package.rpm', 'somefile'])
        ]
        outputs = [b'2.3.1', b'package', b'2.2.4', b'package']

        def cmd_output(command):
            if '-q' in command:
                raise Exception('rpm not installed')
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

    @patch('subprocess.check_output')
    @patch('os.walk')
    def test_find_package_version_not_found(self, mock_walk, mock_run):
        mock_walk.return_value = [
            ('/foo', ['bar', 'zez'], ['baz']),
            ('/foo/bar', [], ['spam', 'package.rpm']),
            ('/foo/zez', [], ['package.rpm', 'somefile'])
        ]
        outputs = [b'another_non_matching_name', b'not_matching_name']

        def cmd_output(command):
            if '-q' in command:
                raise Exception('rpm not installed')
            return outputs.pop()

        mock_run.side_effect = cmd_output
        try:
            find_package_version('package', '/foo') == '2.3.1'
        except Exception as e:
            assert 'Package version not found' in str(e)
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
        'replace_using_package_version.'
        'replace_using_package_version.apply_regex_to_file'
    ))
    @patch((
        'replace_using_package_version.'
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
            '--regex': 'regex',
            '--parse-version': 'minor'
        }
        mock_find_pkg.return_value = '0.0.1'
        main()
        mock_find_pkg.assert_called_once_with(
            'package', './repos'
        )
        mock_apply_regex.assert_called_once_with(
            'file', 'outdir/file', 'regex', '0.0'
        )

    @patch((
        'replace_using_package_version.'
        'replace_using_package_version.find_match_in_version'
    ))
    @patch((
        'replace_using_package_version.'
        'replace_using_package_version.apply_regex_to_file'
    ))
    @patch((
        'replace_using_package_version.'
        'replace_using_package_version.find_package_version'
    ))
    @patch('docopt.docopt')
    @patch('os.path.isdir')
    @patch('os.path.isfile')
    def test_main_package_parse_version(
        self, mock_isfile, mock_isdir, mock_docopt,
        mock_find_pkg, mock_apply_regex, mock_match_version
    ):
        mock_isdir.return_value = True
        mock_isfile.return_value = True
        mock_docopt.return_value = {
            '--package': 'package',
            '--file': 'file',
            '--outdir': 'outdir',
            '--regex': 'regex',
            '--parse-version': 'minor'
        }
        mock_find_pkg.return_value = '0.0.1'
        mock_match_version.return_value = '0.0'
        main()
        mock_find_pkg.assert_called_once_with(
            'package', './repos'
        )
        mock_apply_regex.assert_called_once_with(
            'file', 'outdir/file', 'regex', '0.0'
        )
        mock_match_version.assert_called_once_with(
            version_regex['minor'], '0.0.1'
        )

    @patch((
        'replace_using_package_version.'
        'replace_using_package_version.find_package_version'
    ))
    @patch('docopt.docopt')
    @patch('os.path.isdir')
    @patch('os.path.isfile')
    def test_main_package_parse_version_invalid_argument(
        self, mock_isfile, mock_isdir, mock_docopt, mock_find_pkg
    ):
        mock_find_pkg.return_value = '1.34.2'
        mock_isdir.return_value = True
        mock_isfile.return_value = True
        mock_docopt.return_value = {
            '--package': 'package',
            '--file': 'file',
            '--outdir': 'outdir',
            '--regex': 'regex',
            '--parse-version': 'invalid-value'
        }
        exception = False
        try:
            main()
        except Exception as e:
            assert 'Invalid value for this flag.' in str(e)
            exception = True
        assert exception

    @patch((
        'replace_using_package_version.'
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

    @patch('subprocess.check_output')
    def test_run_command(self, mock_check_output):
        mock_check_output.return_value = b'stdout'
        assert run_command(['/bin/dummycmd', 'arg1']) == 'stdout'

    @patch((
        'replace_using_package_version.'
        'replace_using_package_version.main'
    ))
    def test_main(self, mock_main):
        init('__main__')
        assert mock_main.called
