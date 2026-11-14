# Libraries and distribution

## Library sources and distribution status

The current GitHub `main` repo and the full development directory keep two local libraries (garments and portraits). You can also build a code-only package for cases where the libraries are kept outside the plugin. Both modes support environment variables that point to external library directories.

For asset sources, licenses and responsibility notes, see [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) and [PORTRAIT_LIBRARY_NOTICE.md](../PORTRAIT_LIBRARY_NOTICE.md).

| Dependency | Description |
| --- | --- |
| **Pose library** | **Removed from this repository.** Supply your own pose reference images (for example, connect a LoadImage node to `pose_image`). |
| **Garment library** | **Included in the main GitHub repo** (`garments/`: 1407 garment reference images and an index). The code-only package excludes it by default. |
| **Portrait library** | **Included in the main GitHub repo as a compressed version** (`portraits/`: 1499 WebP images, thumbnails and an index). The code-only package excludes it by default. |
| **Gallery pages and routes** | Provided by this plugin (`web/garment_gallery.html` and the `/aicg3d_pose/*` routes). It calls no external plugins. |
| **Model weights** | The standard `models/` directory (see the tables below). |

> To use it, others only need to: ① copy the whole plugin directory into their `custom_nodes/`; ② prepare the weight files listed under "Required models" below; ③ restart. The GitHub main repo includes the local garment and portrait libraries. With the code-only package, point the `AICG3D_*_LIBRARY` environment variables at external asset directories.

## First-time portrait library setup

The GitHub `main` repo includes `portraits/img/` and `portraits/data/`. If you downloaded the code-only package, or an installer copied only the source, the page shows "Portrait library not installed yet". In that case, configure an external library with the command below, or download the full repo from GitHub.

First obtain a compatible `comfyui-portrait-gallery/library` from a legitimate source, then run:

```bash
python scripts/configure_portrait_library.py --source "C:\path\to\comfyui-portrait-gallery\library"
```

After restarting, click "Browse portrait library" in the node to search. You can also put the library in the plugin's `portraits/` directory or set the `AICG3D_PORTRAIT_LIBRARY` environment variable. The install status endpoint is `/aicg3d_pose/portraits/status`.

## Portrait reference node: face/head-swap reference selection

`PoseQwen21PortraitSelect` picks a front-facing or styled reference from the portrait library. It outputs `portrait_image`, `portrait_id`, `description` and `attribution`. Connect `portrait_image` to the identity reference input of the face/head-swap chain. The node doesn't run anything by itself.

- Library source: [AI モデル顔データベース (AI Model Face Database)](https://ai-portrait-gallery.pages.dev/), original author [あぎ (@agi_aibusi)](https://x.com/agi_aibusi).
- The original site is labeled CC0 1.0, but it also asks people to avoid directly redistributing the image data itself. To meet open-source distribution needs, this plugin includes a compressed copy. `PORTRAIT_LIBRARY_NOTICE.md` keeps that request and a reminder to check compliance yourself.
- The assets are stored in the plugin's `portraits/`: 1499 reference WebP images of up to 768×960, plus 360×450 WebP thumbnails, about 148 MiB in total.
- The portrait node reads the plugin's own `portraits/`. It doesn't depend on the `E:` drive, an external library plugin or a user cache.
- Every card and detail page keeps the original site, original author and CC0 license link. The full notice is in `PORTRAIT_LIBRARY_NOTICE.md`.
- This node is an independent, unofficial local indexing tool. It isn't an official version of the original author's work and has no endorsement from them. Don't use it to impersonate real people or for illegal purposes.
