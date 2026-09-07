"""Build a Kodi repository from the exact ZIP attached to a stable GitHub release."""
import argparse
import hashlib
import html
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

SOURCE = 'anicat-org/plugin.video.anicat'
BASE_URL = 'https://anicat-org.github.io/repository.anicat'
REPO_VERSION = '1.0.0'


def release_zip(tag):
    if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Expected a stable vX.Y.Z release tag')
    release = json.loads(subprocess.check_output(['gh', 'release', 'view', tag, '--repo', SOURCE,
                                                  '--json', 'isDraft,isPrerelease,assets']))
    if release['isDraft'] or release['isPrerelease']:
        raise ValueError('Only published stable releases are distributed')
    asset = next(a for a in release['assets'] if a['name'] == 'plugin.video.anicat-' + tag + '.zip')
    expected_url = 'https://github.com/' + SOURCE + '/releases/download/' + tag + '/' + asset['name']
    if asset['url'] != expected_url:
        raise ValueError('Unexpected release asset URL')
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run(['gh', 'release', 'download', tag, '--repo', SOURCE, '--pattern', asset['name'],
                        '--dir', directory], check=True)
        data = (Path(directory) / asset['name']).read_bytes()
    if asset.get('digest') and asset['digest'] != 'sha256:' + hashlib.sha256(data).hexdigest():
        raise ValueError('Release asset checksum mismatch')
    return data


def write_xml(node):
    ET.indent(node, space='  ')
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(node, encoding='utf-8') + b'\n'


def build(data, output, base_url=BASE_URL, expected_version=None):
    output = Path(output)
    if not base_url.startswith('https://'):
        raise ValueError('Repository must use HTTPS')
    base_url = base_url.rstrip('/')
    with ZipFile(io.BytesIO(data)) as archive:
        if archive.testzip() is not None:
            raise ValueError('Invalid ZIP CRC')
        addon = ET.fromstring(archive.read('plugin.video.anicat/addon.xml'))
        version = addon.get('version', '')
        if addon.get('id') != 'plugin.video.anicat' or not re.fullmatch(r'\d+\.\d+\.\d+', version):
            raise ValueError('Unexpected addon or version')
        if expected_version and version != expected_version:
            raise ValueError('Release tag and addon manifest differ')
        addon_dir = output / 'plugin.video.anicat'
        addon_dir.mkdir(parents=True, exist_ok=True)
        for asset in addon.findall("extension[@point='xbmc.addon.metadata']/assets/*"):
            name = asset.text or ''
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name:
                raise ValueError('Unsafe asset path')
            target = addon_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read('plugin.video.anicat/' + name))
        icon = archive.read('plugin.video.anicat/resources/media/icon.png')
    package_name = 'plugin.video.anicat-' + version + '.zip'
    (addon_dir / package_name).write_bytes(data)
    (addon_dir / (package_name + '.sha256')).write_text(hashlib.sha256(data).hexdigest() + '\n', encoding='ascii')
    (addon_dir / 'addon.xml').write_bytes(write_xml(addon))
    news = addon.findtext("extension[@point='xbmc.addon.metadata']/news", '')
    (addon_dir / ('changelog-' + version + '.txt')).write_text(news, encoding='utf-8')

    repo = ET.fromstring('''<addon id="repository.anicat" name="AniCAT Repository" version="1.0.0" provider-name="AniCAT">
      <requires><import addon="xbmc.addon" version="12.0.0" /></requires>
      <extension point="xbmc.addon.repository" name="AniCAT Repository"><dir minversion="21.0.0">
        <info /><checksum /><datadir /><hashes>false</hashes>
      </dir></extension>
      <extension point="xbmc.addon.metadata">
        <summary lang="es_ES">Repositorio de instalación y actualizaciones de AniCAT</summary>
        <description lang="es_ES">Instala AniCAT y recibe sus versiones estables. Requiere Kodi 21 o posterior.</description>
        <platform>all</platform><license>MIT</license>
        <source>https://github.com/anicat-org/repository.anicat</source>
        <assets><icon>icon.png</icon></assets>
      </extension></addon>''')
    repo.set('version', REPO_VERSION)
    directory = repo.find("extension[@point='xbmc.addon.repository']/dir")
    for name, suffix in [('info', '/addons.xml'), ('checksum', '/addons.xml.md5'), ('datadir', '/')]:
        directory.find(name).text = base_url + suffix
    repo_xml = write_xml(repo)
    repo_dir = output / 'repository.anicat'
    repo_dir.mkdir(exist_ok=True)
    repo_package = 'repository.anicat-' + REPO_VERSION + '.zip'
    with ZipFile(repo_dir / repo_package, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('repository.anicat/addon.xml', repo_xml)
        archive.writestr('repository.anicat/icon.png', icon)
    (repo_dir / 'addon.xml').write_bytes(repo_xml)
    (repo_dir / 'icon.png').write_bytes(icon)
    root = ET.Element('addons')
    root.extend([repo, addon])
    index = write_xml(root)
    (output / 'addons.xml').write_bytes(index)
    (output / 'addons.xml.md5').write_text(hashlib.md5(index).hexdigest(), encoding='ascii')
    (output / '.nojekyll').write_text('')
    for folder, filename in [(repo_dir, repo_package), (addon_dir, package_name)]:
        (folder / 'index.html').write_text('<!doctype html><meta charset="utf-8"><a href="../">../</a><br><a href="' + filename + '">' + filename + '</a>', encoding='utf-8')
    (output / 'descargar.html').write_text('''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
      <title>AniCAT · Repositorio Kodi</title><style>body{background:#101012;color:#eee;font:18px system-ui;max-width:760px;margin:60px auto;padding:24px}a{color:#ff666e}img{width:88px;border-radius:24px}li{margin:16px 0}.download{display:inline-block;background:#d90819;color:white;padding:16px 24px;border-radius:10px;text-decoration:none}</style>
      <img src="repository.anicat/icon.png" alt="AniCAT"><h1>AniCAT para Kodi</h1><p>Instala el repositorio una vez y recibe las nuevas versiones estables. Kodi 21 o posterior.</p>
      <p><a class="download" href="repository.anicat/''' + repo_package + '''">Descargar repositorio AniCAT</a></p>
      <ol><li>En Kodi, permite los orígenes desconocidos para instalar nuestro ZIP.</li><li>Abre Add-ons → Instalar desde un archivo .zip y selecciona el repositorio descargado.</li><li>En Instalar desde repositorio → AniCAT Repository → Add-ons de vídeo, instala AniCAT.</li><li>Mantén activadas las actualizaciones automáticas de AniCAT.</li></ol>
      <p>Dependencias: Google Drive y Cloud Drive Common, disponibles en el repositorio oficial de Kodi. Si Kodi solicita una dependencia, comprueba que ese repositorio está habilitado.</p>
      <p>Versión del addon: ''' + html.escape(version) + ''' · <a href="plugin.video.anicat/''' + package_name + '''">ZIP del addon</a></p>
      <p><a href="plugin.video.anicat/changelog-''' + version + '''.txt">Novedades</a> · <a href="repository.anicat/">Archivos del repositorio</a></p></html>''', encoding='utf-8')
    (output / repo_package).write_bytes((repo_dir / repo_package).read_bytes())
    (output / 'index.html').write_text(
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Index of /</title></head>'
        '<body><h1>Index of /</h1><hr><pre><a href="' + repo_package + '">'
        + repo_package + '</a></pre><hr></body></html>\n', encoding='utf-8')
    return version


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--zip', type=Path)
    parser.add_argument('--output', type=Path, default=Path('site'))
    parser.add_argument('--base-url', default=BASE_URL)
    args = parser.parse_args()
    tag = json.loads(Path('release.json').read_text())['tag']
    package = args.zip or Path('packages') / ('plugin.video.anicat-' + tag + '.zip')
    data = package.read_bytes()
    print('Built AniCAT', build(data, args.output, args.base_url, tag.removeprefix('v')))
