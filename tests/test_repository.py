import hashlib
import io
import tempfile
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from tools.build_repository import build


class RepositoryTests(unittest.TestCase):
    def package(self, version='1.5.5', asset='resources/icon.png'):
        output = io.BytesIO()
        with ZipFile(output, 'w') as archive:
            archive.writestr('plugin.video.anicat/addon.xml', f'''<addon id="plugin.video.anicat" version="{version}"><extension point="xbmc.addon.metadata"><assets><icon>{asset}</icon></assets></extension></addon>''')
            archive.writestr('plugin.video.anicat/' + asset, b'icon')
            archive.writestr('plugin.video.anicat/resources/media/icon.png', b'icon')
        return output.getvalue()

    def test_index_bootstrap_package_and_original_zip(self):
        with tempfile.TemporaryDirectory() as folder:
            data = self.package()
            build(data, folder, expected_version='1.5.5')
            root = Path(folder)
            index = (root / 'addons.xml').read_bytes()
            self.assertEqual((root / 'addons.xml.md5').read_text(), hashlib.md5(index).hexdigest())
            self.assertEqual({node.get('id') for node in ET.fromstring(index)}, {'repository.anicat', 'plugin.video.anicat'})
            self.assertEqual((root / 'plugin.video.anicat/plugin.video.anicat-1.5.5.zip').read_bytes(), data)
            self.assertEqual((root / 'repository.anicat-1.0.0.zip').read_bytes(),
                             (root / 'repository.anicat/repository.anicat-1.0.0.zip').read_bytes())
            self.assertIn('href="repository.anicat-1.0.0.zip"', (root / 'index.html').read_text())
            self.assertTrue((root / 'descargar.html').exists())
            with ZipFile(root / 'repository.anicat/repository.anicat-1.0.0.zip') as archive:
                self.assertIsNone(archive.testzip())
                manifest = ET.fromstring(archive.read('repository.anicat/addon.xml'))
                self.assertEqual(manifest.findtext('extension/dir/info'), 'https://anicat-org.github.io/repository.anicat/addons.xml')

    def test_version_mismatch_and_unsafe_assets_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError): build(self.package(), folder, expected_version='1.5.6')
            with self.assertRaises(ValueError): build(self.package(asset='../escape'), folder)

    def test_custom_domain_and_https(self):
        with tempfile.TemporaryDirectory() as folder:
            build(self.package(), folder, base_url='https://repo.ani.cat/')
            root = ET.parse(Path(folder) / 'addons.xml')
            self.assertEqual(root.findtext('addon/extension/dir/info'), 'https://repo.ani.cat/addons.xml')
            with self.assertRaises(ValueError): build(self.package(), folder, base_url='http://example.com')
