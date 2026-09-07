"""Create Kodi's HTTP file source from the already built repository package."""
import argparse
from pathlib import Path
import shutil
from zipfile import ZipFile
import xml.etree.ElementTree as ET


def build_source(site, output):
    site, output = Path(site), Path(output)
    manifest = ET.parse(site / 'repository.anicat' / 'addon.xml').getroot()
    filename = 'repository.anicat-' + manifest.attrib['version'] + '.zip'
    package = site / 'repository.anicat' / filename
    with ZipFile(package) as archive:
        if archive.testzip() is not None:
            raise ValueError('Invalid repository ZIP')
    output.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(package, output / filename)
    # Keep previous versions downloadable, but only advertise the current installer.
    (output / 'index.html').write_text(
        '<!DOCTYPE html>\n<html><head><meta charset="utf-8">'
        '<title>Index of /</title></head><body>\n<h1>Index of /</h1>\n'
        '<hr>\n<pre><a href="' + filename + '">' + filename + '</a></pre>\n'
        '<hr>\n</body></html>\n', encoding='utf-8')
    (output / '.nojekyll').touch()
    return filename


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', type=Path, default=Path('site'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(build_source(args.site, args.output))
