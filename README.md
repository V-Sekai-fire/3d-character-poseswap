# 3d-character-poseswap

The source code is under the MIT License. See [LICENSE](LICENSE) for the copyright notice and [AUTHORS.md](AUTHORS.md) for upstream authors and asset sources.

> [!IMPORTANT]
> This repository is not an asset pack with cleared rights. Third-party assets are in the repository, but that doesn't mean the project author owns, licenses, endorses or guarantees them for redistribution or commercial use.
> MIT covers only the project source code. The images and indexes in `garments/` and `portraits/` are third-party assets outside MIT. Model weights are not shipped with the repository.
> The pose library has been removed from this repository. No license was found for the garment library that covers redistribution. The portrait library is labeled CC0, but it also asks that it not be redistributed. Before you publish the full asset pack, read [LEGAL_AND_SAFETY.md](LEGAL_AND_SAFETY.md), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md). A disclaimer is not a substitute for permission.
>
> Before use, read [DISCLAIMER.md](DISCLAIMER.md), [NOTICE](NOTICE) and [AUTHORS.md](AUTHORS.md) in full. If you are a rights holder and think some content shouldn't be distributed, contact the author through a GitHub Issue to have it taken down.
>
> Content notice: the garment index includes adult-oriented categories. The project is for adults only. Do not use it to sexualize minors, to sexualize anyone without consent, to impersonate real people, or for any other illegal purpose.

A standalone plugin. Its pipeline is **swap head and hair → swap pose with Qwen Image 2.1 → swap the full outfit**. You can also use Qwen-Image-Edit-2511 for a single high-fidelity outfit swap.

The recommended setup is the "dual-wrapper" workflow. One subgraph takes the four asset inputs, and one "one-click replace" subgraph does the swaps. Each of the three results goes from its own output to a standard PreviewImage node.

"I generate a character and pick a pose, and the character comes out in that pose. I pick an outfit, and they change clothes on the spot."

## Installation

The project needs no extra `pip install`. Image loading uses Pillow, NumPy and PyTorch.

```bash
cd custom_nodes
git clone https://github.com/V-Sekai-fire/3d-character-poseswap.git
```

Then download the model weights, which the repo doesn't include, as described in [MODEL_REQUIREMENTS.md](MODEL_REQUIREMENTS.md), and restart.
Build a code-only release package with `python scripts/package_open_source.py`. It excludes the third-party libraries by default.

## Documentation

- [Libraries and distribution](docs/libraries.md): Garment and portrait libraries, sources, licenses, setup
- [Nodes and usage](docs/nodes.md): Node reference, wiring, usage steps, environment variables
- [Workflows](docs/workflows.md): Example workflows and how to run them
- [How it works](docs/how-it-works.md): The pose-swap and outfit-swap pipelines
- [Required models](docs/models.md): Model weights and default sampling
- [Verification](docs/verification.md): Upstream verification notes
