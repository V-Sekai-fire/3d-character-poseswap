# 3d-character-poseswap

See [LICENSE](LICENSE) for the copyright notice and [AUTHORS.md](AUTHORS.md) for upstream authors and asset sources.

> [!IMPORTANT]
> This repository is not an asset pack with cleared rights. Third-party assets are in the repository, but that doesn't mean the project author owns, licenses, endorses or guarantees them for redistribution or commercial use.
> The images and indexes in `garments/` and `portraits/` are third-party assets. They are not covered by the MIT license in `LICENSE`.
> No license was found for the garment library that covers redistribution. The portrait library is labeled CC0, but it also asks that it not be redistributed. Before you publish the full asset pack, read [LEGAL_AND_SAFETY.md](LEGAL_AND_SAFETY.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). A disclaimer is not a substitute for permission.
>
> Before use, read [DISCLAIMER.md](DISCLAIMER.md), [NOTICE](NOTICE) and [AUTHORS.md](AUTHORS.md) in full. If you are a rights holder and think some content shouldn't be distributed, contact the author through a GitHub Issue to have it taken down.
>
> Content notice: the garment index includes adult-oriented categories. The dataset is for adults only. Do not use it to sexualize minors, to sexualize anyone without consent, to impersonate real people, or for any other illegal purpose.

A dataset of character reference images for 3D character and outfit work. It has two collections, each with a metadata index:

- **Garments** (`garments/`): 1407 garment reference images. `data/garment.json` lists each record's `id`, `cat` (category), `cat_cn` (Chinese category name), `desc` (description) and `img` (image path).
- **Portraits** (`portraits/`): 1499 face and hairstyle reference images as WebP, up to 768×960, with 360×450 thumbnails. `data/portrait-zh.json` lists each record's `id`, `section`, `hair`, `style`, image sizes, file paths and Chinese labels. `data/meta-zh.json` holds collection-level metadata.

The images were originally collected for a pipeline that swaps a character's head and hair, pose and outfit with Qwen Image 2.1 and Qwen-Image-Edit-2511. This repository no longer contains that code. A pose library that used to be part of it has also been removed.

## Documentation

- [Libraries and distribution](docs/libraries.md): Garment and portrait libraries, sources, licenses, setup
- [Nodes and usage](docs/nodes.md): Node reference, wiring, usage steps, environment variables
- [Workflows](docs/workflows.md): Example workflows and how to run them
- [How it works](docs/how-it-works.md): The pose-swap and outfit-swap pipelines
- [Required models](docs/models.md): Model weights and default sampling
- [Verification](docs/verification.md): Upstream verification notes
