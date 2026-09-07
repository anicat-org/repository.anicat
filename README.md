# AniCAT Repository

**Fuente para el gestor de archivos de Kodi: https://anicat-org.github.io/**
El índice de esa raíz muestra directamente el ZIP instalable del repositorio.
Tras publicar, el workflow sincroniza el índice y el ZIP en
`anicat-org/anicat-org.github.io` usando `KODI_FILE_SOURCE_DEPLOY_KEY`, una clave
SSH con escritura limitada a ese repositorio público.

Repositorio instalable para Kodi 21 o posterior, publicado en:

https://anicat-org.github.io/repository.anicat/

Descarga `repository.anicat/repository.anicat-1.0.0.zip`, instálalo desde un ZIP en
Kodi y abre **Instalar desde repositorio → AniCAT Repository → Add-ons de vídeo**.
Las actualizaciones dependen de tenerlas habilitadas en Kodi. Google Drive 1.5.0
y Cloud Drive Common 1.4.0 están disponibles en el repositorio oficial de Kodi.

## Publicación

`release.json` fija el tag estable que se distribuye. El workflow del addon descarga el ZIP
original de GitHub Releases usando su token de Actions (el código fuente es privado), verifica su checksum cuando GitHub lo proporciona,
comprueba su versión y construye el índice, los assets y los paquetes instalables.
El ZIP original se conserva byte a byte con el nombre requerido por Kodi, sin `v`.
El contenido generado en `site/` no se versiona. `packages/` contiene los ZIP
distribuibles públicos; el despliegue de Pages no necesita acceso al repositorio privado.

El repositorio del addon actualiza `release.json` al publicar una release estable,
mediante una deploy key SSH limitada a este repositorio. También puede ejecutarse
manualmente su workflow de publicación para republicar una versión existente.
El push activa el despliegue de Pages. No se distribuyen borradores ni prereleases.
La versión de `repository.anicat` es independiente de la versión de AniCAT.

Desarrollo local:

```sh
python -m unittest discover -s tests -v
python tools/build_repository.py --zip ../plugin.video.anicat-v1.5.5.zip
```

`addons.xml.md5` es el indicador de cambios de Kodi. Los paquetes se sirven por
HTTPS; se publica además su SHA-256. `hashes=false` evita exigir cabeceras
`Content-SHA256` que GitHub Pages no proporciona; no desactiva HTTPS ni la
verificación de la release al construir el repositorio.

## Dominio propio

`repo.ani.cat` está configurado en Pages de este repositorio, con CNAME DNS
hacia `anicat-org.github.io` y HTTPS. El índice de archivos y el ZIP se publican
junto a `addons.xml` en la raíz. La landing se conserva en `descargar.html`.
GitHub redirige las URL anteriores del sitio de proyecto al dominio propio.

La fuente alternativa https://anicat-org.github.io/ también sirve el instalador.
El instalador 1.0.0 conserva sus URL originales, compatibles mediante esa
redirección. Una futura migración de URL internas requiere aumentar su versión.
