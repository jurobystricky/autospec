import unittest
from unittest.mock import Mock, patch
import config
import tarball


# Stores all test cases for dynamic tests.
# In order to add more tests just add more elements to the lists provided below.

CONTENT_PREFIX = [
    'common-prefix/',
    'common-prefix/md5/',
    'common-prefix/md5/CMakeLists.txt',
    'common-prefix/md5/md5.h',
    'common-prefix/md5/md5hl.c',
    'common-prefix/md5/md5cmp.c',
    'common-prefix/md5/md5.c',
    'common-prefix/md5/Makefile.am',
    'common-prefix/md5/Makefile.in',
    'common-prefix/jerror.c',
    'common-prefix/sharedlib/',
    'common-prefix/sharedlib/CMakeLists.txt',
    'common-prefix/turbojpeg-mapfile',
    'common-prefix/jdpostct.c',
    'common-prefix/turbojpeg-jni.c',
]

CONTENT_SUBDIR = [
    'dir1/',
    'dir1/md5/',
    'dir1/md5/CMakeLists.txt',
    'dir1/md5/md5.h',
    'dir1/md5/md5hl.c',
    'dir1/md5/md5cmp.c',
    'dir1/md5/md5.c',
    'dir1/md5/Makefile.am',
    'dir1/md5/Makefile.in',
    'dir2/',
    'dir2/jerror.c',
    'dir2/sharedlib/',
    'dir2/sharedlib/CMakeLists.txt',
    'dir2/turbojpeg-mapfile',
    'dir2/jdpostct.c',
    'dir2/turbojpeg-jni.c',
    'file.c'
]

# Input for tarball.Source class tests.
# Structure: (url, destination, path, fake-content, source_type, prefix, subddir)
SRC_CREATION = [
    ("https://example/src-prefix.zip", "", "/tmp/src-prefix.zip", CONTENT_PREFIX, "zip", "common-prefix", None),
    ("https://example/src-subdir.zip", "", "/tmp/src-subdir.zip", CONTENT_SUBDIR, "zip", "", "src-subdir"),
    ("https://example/src-prefix.tar", "", "/tmp/src-prefix.tar", CONTENT_PREFIX, "tar", "common-prefix", None),
    ("https://example/src-subdir.tar", "", "/tmp/src-subdir.tar", CONTENT_SUBDIR, "tar", "", "src-subdir"),
    ("https://example/src-no-extractable.tar", ":", "/tmp/src-no-extractable.tar", None, None, None, None),
    ("https://example/go-src/list", "", "/tmp/list", None, "go", "", "list"),
]

# Input for tarball.detect_build_from_url method tests
# Structure: (url, build_pattern)
BUILD_PAT_URL = [
    ("https://cran.r-project.org/src/contrib/raster_3.0-12.tar.gz", "R"),
    ("http://pypi.debian.net/argparse/argparse-1.4.0.tar.gz", "distutils3"),
    ("https://pypi.python.org/packages/source/T/Tempita/Tempita-0.5.2.tar.gz", "distutils3"),
    ("https://cpan.metacpan.org/authors/id/T/TO/TODDR/IO-Tty-1.14.tar.gz", "cpan"),
    ("http://search.cpan.org/CPAN/authors/id/D/DS/DSKOLL/IO-stringy-2.111.tar.gz", "cpan"),
    ("https://proxy.golang.org/github.com/spf13/pflag/@v/list", "godep"),
    ("https://pecl.php.net//get/lua-2.0.6.tgz", "phpize"),
]


class MockSrcFile():
    """Mock class for zipfile and tarfile."""

    def __init__(self, path, mode):
        self.name = path
        self.mode = mode

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        return False

    @classmethod
    def set_content(cls, content):
        cls.content = content

    def getnames(self):
        return self.content

    def namelist(self):
        return self.content


def source_test_generator(url, destination, path, content, src_type, prefix, subdir):
    """Create test for tarball.Source class using generator template."""

    @patch('tarball.tarfile.open', MockSrcFile)
    @patch('tarball.zipfile.ZipFile', MockSrcFile)
    @patch('tarball.tarfile.is_tarfile', Mock(return_value=True))
    @patch('tarball.zipfile.is_zipfile', Mock(return_value=True))
    def generator(self):
        """Test template."""
        # Set fake content
        MockSrcFile.set_content(content)
        src = tarball.Source(url, destination, path)
        self.assertEqual(src.type, src_type)
        self.assertEqual(src.prefix, prefix)
        self.assertEqual(src.subdir, subdir)

    return generator


def detect_build_test_generator(url, build_pattern):
    """Create test for tarball.detect_build_from_url method."""
    def generator(self):
        """Test template."""
        tarball.detect_build_from_url(url)
        self.assertEqual(build_pattern, tarball.buildpattern.default_pattern)

    return generator


def name_and_version_test_generator(url, name, version):
    """Create test for tarball.name_and_version method."""
    def generator(self):
        """Test template."""
        conf = config.Config()
        conf.parse_config_versions = Mock(return_value={})
        tarball.url = url
        n, _, v = tarball.name_and_version('', '', Mock(), conf)
        self.assertEqual(name, n)
        self.assertEqual(version, v)
        if "github.com" in url:
            self.assertRegex(tarball.giturl, r"https://github.com/[^/]+/" + tarball.repo + ".git")

    return generator


def create_dynamic_tests():
    """Create dynamic tests based on content in lists and packageulrs file."""
    # Create tests for tarball.Source class.
    for url, dest, path, content, src_type, prefix, subdir in SRC_CREATION:
        test_name = 'test_src_{}'.format(url)
        test = source_test_generator(url, dest, path, content, src_type, prefix, subdir)
        setattr(TestTarball, test_name, test)

    # Create tests for tarball.detect_build_from_url method.
    for url, build_pattern in BUILD_PAT_URL:
        test_name = 'test_pat_{}'.format(url)
        test = detect_build_test_generator(url, build_pattern)
        setattr(TestTarball, test_name, test)

    # Create tests for tarball.name_and_version method.
    with open('tests/packageurls', 'r') as pkgurls:
        for urlline in pkgurls.read().split('\n'):
            if not urlline or urlline.startswith('#'):
                continue
            (url, name, version) = urlline.split(',')
            test_name = 'test_name_ver_{}'.format(url)
            test = name_and_version_test_generator(url, name, version)
            setattr(TestTarball, test_name, test)


class TestTarball(unittest.TestCase):
    """Main testing class for tarball.py.

    This class would contain all static tests and dynamic tests for tarball.py
    """

    def setUp(self):
        """Set up default values before start test."""
        # Set strenght to 0 so it can be updated during tests
        tarball.build.base_path = '/tmp'
        tarball.build.download_path = '/download/path/'

    def tearDown(self):
        """Clean up after running each test."""
        tarball.build.base_path = None
        tarball.build.download_path = None
        tarball.buildpattern.archive_details = {}
        tarball.buildpattern.pattern_strength = 0
        tarball.buildpattern.sources['godep'] = []
        tarball.buildpattern.sources['version'] = []
        tarball.gcov_file = ''
        tarball.giturl = ''
        tarball.name = ''
        tarball.prefixes = {}
        tarball.repo = ''
        tarball.url = ''
        tarball.version = ''

    @patch('tarball.os.path.isfile', Mock(return_value=True))
    def test_set_gcov(self):
        """Test for tarball.set_gcov method."""
        # Set up input values
        tarball.name = 'test'
        tarball.set_gcov()
        self.assertEqual(tarball.gcov_file, 'test.gcov')

    def test_process_go_archives(self):
        """Test for tarball.process_go_archives method."""
        # Set up input values
        tarball.url = 'https://proxy.golang.org/github.com/!burnt!sushi/toml/@v/list'
        tarball.multi_version = ['v0.3.1', 'v0.3.0', 'v0.2.0']
        go_archives = []
        go_archives_expected = [
            "https://proxy.golang.org/github.com/!burnt!sushi/toml/@v/v0.3.1.info", ":",
            "https://proxy.golang.org/github.com/!burnt!sushi/toml/@v/v0.3.1.mod", ":",
            "https://proxy.golang.org/github.com/!burnt!sushi/toml/@v/v0.3.1.zip", "",
            "https://proxy.golang.org/github.com/!burnt!sushi/toml/@v/v0.3.0.info", ":",
            "https://proxy.golang.org/github.com/!burnt!sushi/toml/@v/v0.3.0.mod", ":",
            "https://proxy.golang.org/github.com/!burnt!sushi/toml/@v/v0.3.0.zip", "",
            "https://proxy.golang.org/github.com/!burnt!sushi/toml/@v/v0.2.0.info", ":",
            "https://proxy.golang.org/github.com/!burnt!sushi/toml/@v/v0.2.0.mod", ":",
            "https://proxy.golang.org/github.com/!burnt!sushi/toml/@v/v0.2.0.zip", "",
        ]
        tarball.process_go_archives(go_archives)
        self.assertEqual(go_archives, go_archives_expected)

    def test_process_multiver_archives(self):
        """Test for tarball.process_multiver_archives method."""
        # Set up input values
        main_src = tarball.Source('https://example/src-5.0.tar', ':', '/tmp/src.tar')
        multiver_archives = []
        config_versions = {
            '5.0': 'https://example/src-5.0.tar',
            '4.0': 'https://example/src-4.0.tar',
            '3.5': 'https://example/src-3.5.tar',
            '3.0': 'https://example/src-3.0.tar',
        }
        expected_multiver_archives = [
            'https://example/src-4.0.tar', '',
            'https://example/src-3.5.tar', '',
            'https://example/src-3.0.tar', '',
        ]
        # Set up a return value for parse_config_versions method
        attrs = {'parse_config_versions.return_value': config_versions}
        conf = Mock()
        conf.configure_mock(**attrs)
        tarball.process_multiver_archives(main_src, multiver_archives, conf)
        self.assertEqual(multiver_archives, expected_multiver_archives)

    @patch('tarball.Source.set_prefix', Mock())
    @patch('tarball.Source.extract', Mock())
    def test_extract_sources(self):
        """Test for tarball.extract_sources method."""
        # Set up input values
        main_src = tarball.Source('https://example1.tar', '', '/tmp')
        arch1_src = tarball.Source('https://example2.tar', '', '/tmp')
        arch2_src = tarball.Source('https://example3.tar', ':', '/tmp')
        arch3_src = tarball.Source('https://example4.tar', '', '/tmp')
        archives_src = [arch1_src, arch2_src, arch3_src]
        tarball.extract_sources(main_src, archives_src)
        # Sources with destination=':' should not be extracted, so method
        # should be called only 3 times.
        self.assertEqual(tarball.Source.extract.call_count, 3)


# Create dynamic tests based on config file
create_dynamic_tests()

if __name__ == '__main__':
    unittest.main(buffer=True)
