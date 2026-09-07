import tempfile
from pathlib import Path
from html.parser import HTMLParser
from zipfile import ZipFile
import unittest

from tools.build_file_source import build_source


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs)['href'])


class FileSourceTests(unittest.TestCase):
    def test_root_link_resolves_to_original_installer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            repository = root / 'site' / 'repository.anicat'
            repository.mkdir(parents=True)
            (repository / 'addon.xml').write_text('<addon version="1.0.1"/>')
            package = repository / 'repository.anicat-1.0.1.zip'
            with ZipFile(package, 'w') as archive:
                archive.writestr('repository.anicat/addon.xml', '<addon/>')
            output = root / 'public'
            build_source(root / 'site', output)
            parser = Links()
            parser.feed((output / 'index.html').read_text())
            self.assertEqual(parser.links, [package.name])
            self.assertEqual((output / parser.links[0]).read_bytes(), package.read_bytes())
            self.assertTrue((output / '.nojekyll').exists())
