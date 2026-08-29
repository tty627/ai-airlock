# AI Airlock Third-Party Notices

> Status: source-submission notice for the `v0.1.0-rc.3` candidate.
> AI Airlock itself is licensed under Apache-2.0; this file separately records direct dependencies,
> known optional-extra dependencies, and the model source used by the frozen core evidence.

AI Airlock depends on third-party software and model artifacts governed by their own licenses. Those
licenses remain in effect alongside the project's Apache-2.0 license.

## Direct and declared Python dependencies

| Component | RC declaration / observed version | Purpose | License / upstream source | Distribution note |
|---|---|---|---|---|
| [setuptools](https://pypi.org/project/setuptools/) | `>=75,<81`; exact resolved RC version not recorded | Build backend | [MIT](https://github.com/pypa/setuptools/blob/main/LICENSE) | Build-only; do not claim an exact version from current evidence |
| [PyYAML 6.0.3](https://pypi.org/project/PyYAML/6.0.3/) | declared `>=6.0,<7.0`; evidence `6.0.3` | Runtime YAML policy/config parsing | [MIT](https://github.com/yaml/pyyaml/blob/6.0.3/LICENSE) | Preserve copyright and license text when redistributed |
| [pytest 8.4.2](https://pypi.org/project/pytest/8.4.2/) | declared `>=8.3,<9.0`; evidence `8.4.2` | Development and tests | [MIT](https://github.com/pytest-dev/pytest/blob/8.4.2/LICENSE) | Development-only |
| [Ruff 0.16.5](https://pypi.org/project/ruff/0.16.5/) | declared `>=0.11,<1.0`; evidence `0.16.5` | Lint and formatting checks | [MIT](https://github.com/astral-sh/ruff/blob/0.16.5/LICENSE) | Development-only |
| [huggingface-hub 1.28.0](https://pypi.org/project/huggingface-hub/1.28.0/) | pinned `1.28.0` | Fetch fixed-revision model sources during preparation | [Apache-2.0](https://github.com/huggingface/huggingface_hub/blob/v1.28.0/LICENSE) | Preserve license and any notices in a redistributed environment |
| [NumPy 2.5.2](https://pypi.org/project/numpy/2.5.2/) | pinned `2.5.2` | Pooling, normalization, numeric operations | [NumPy license bundle](https://github.com/numpy/numpy/blob/v2.5.2/LICENSE.txt) | Upstream metadata/source includes BSD-3-Clause and bundled components under 0BSD, MIT, Zlib and CC0-1.0; preserve the actual wheel's `dist-info/licenses/` rather than reducing it to one label |
| [OpenVINO Runtime 2026.3.1](https://pypi.org/project/openvino/2026.3.1/) | pinned `2026.3.1` | Load, compile and execute IR on CPU | [Apache-2.0](https://github.com/openvinotoolkit/openvino/blob/2026.3.1/LICENSE) plus [third-party programs](https://github.com/openvinotoolkit/openvino/blob/2026.3.1/licensing/third-party-programs.txt) | A binary/offline distribution must carry the notices shipped with its actual wheel, including applicable runtime libraries |
| [OpenVINO GenAI 2026.3.1.0](https://pypi.org/project/openvino-genai/2026.3.1.0/) | pinned `2026.3.1.0` | Provides `openvino_genai.Tokenizer`; not used for LLM text generation | [Apache-2.0](https://github.com/openvinotoolkit/openvino.genai/blob/2026.3.1.0/LICENSE) plus [third-party programs](https://github.com/openvinotoolkit/openvino.genai/blob/2026.3.1.0/third-party-programs.txt) | Preserve package notices; do not describe this project as using GenAI content generation |
| [OpenVINO Tokenizers 2026.3.1.0](https://pypi.org/project/openvino-tokenizers/2026.3.1.0/) | pinned `2026.3.1.0` | Convert a Hugging Face tokenizer into OpenVINO tokenizer IR | [Apache-2.0](https://github.com/openvinotoolkit/openvino_tokenizers/blob/2026.3.1.0/LICENSE) plus [third-party programs](https://github.com/openvinotoolkit/openvino_tokenizers/blob/2026.3.1.0/third-party-programs.txt) | Preserve package license and third-party notices |
| [tiktoken 0.14.0](https://pypi.org/project/tiktoken/0.14.0/) | pinned `0.14.0` | Declared conversion-support dependency; RC source does not directly import it | [MIT](https://github.com/openai/tiktoken/blob/0.14.0/LICENSE) | Release evidence does not list the resolved package separately |
| [Transformers 5.16.1](https://pypi.org/project/transformers/5.16.1/) | pinned `5.16.1` with `sentencepiece` extra | Offline `AutoTokenizer` loading and model conversion support | [Apache-2.0](https://github.com/huggingface/transformers/blob/v5.16.1/LICENSE) | Preserve license; actual extra resolution must be frozen before binary/offline redistribution |

## Known dependencies introduced by `transformers[sentencepiece]`

These packages are not directly pinned by AI Airlock, and the frozen release evidence does not record
their resolved versions. They therefore remain a packaging follow-up rather than a complete RC lock.

| Component | Declared/known constraint | License / upstream source | Required follow-up |
|---|---|---|---|
| [SentencePiece](https://github.com/google/sentencepiece) | Transformers extra constrains `>=0.1.91,!=0.1.92`; actual RC version not recorded | [Apache-2.0](https://github.com/google/sentencepiece/blob/master/LICENSE) | Freeze the resolved version and preserve its license before distributing an environment |
| [Protocol Buffers](https://github.com/protocolbuffers/protobuf) | Transitive; actual RC version not recorded | [BSD-3-Clause](https://github.com/protocolbuffers/protobuf/blob/main/LICENSE) | Freeze the resolved version and preserve copyright, conditions and disclaimer |

Other transitive packages may be present. The release evidence explicitly states that the project does
not yet have a complete transitive lock/hash. Before distributing wheels, containers, offline installers
or a bundled runtime, generate an SBOM or equivalent resolved inventory and collect the LICENSE/NOTICE
files from the exact artifacts being shipped.

## Model

| Artifact | Frozen source | Declared license | Use in AI Airlock | Required attribution / review |
|---|---|---|---|---|
| `intfloat/multilingual-e5-small` | [Hugging Face fixed revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`](https://huggingface.co/intfloat/multilingual-e5-small/tree/614241f622f53c4eeff9890bdc4f31cfecc418b3) and [fixed model card](https://huggingface.co/intfloat/multilingual-e5-small/blob/614241f622f53c4eeff9890bdc4f31cfecc418b3/README.md) | Model-card metadata declares `MIT`; that revision does not contain a standalone `LICENSE` or `NOTICE` file | Source files are downloaded at the fixed revision, hash-verified, then locally converted to FP16 OpenVINO IR and tokenizer IR | Preserve model name, upstream owner/repository, revision, declared MIT license and conversion description. Confirm copyright attribution and redistribution terms before hosting converted weights |

The model card states that the model was initialized from
[`microsoft/Multilingual-MiniLM-L12-H384`](https://huggingface.co/microsoft/Multilingual-MiniLM-L12-H384).
That base model's current page declares MIT, but the E5 card does not identify the exact base-model
revision used for initialization. Treat the page only as auxiliary context, not fixed-revision provenance.
This notice does not constitute a rights audit of every dataset named in the E5 model card. Do not claim
that all training-data commercial rights have been independently verified.

## Project license

AI Airlock is licensed under the [Apache License 2.0](LICENSE), copyright 2026 谭天晔. This project license
does not replace or modify the licenses of the third-party software and model artifacts listed above. The decision
record is [`docs/license-decision.md`](docs/license-decision.md).

## Packaging obligations checklist

Before any public or binary distribution:

- keep the AI Airlock Apache-2.0 project license and copyright attribution in the distributed source;
- keep this notice and the project license separate from third-party license texts;
- freeze the complete resolved dependency set for the distributed artifact;
- copy LICENSE/NOTICE and wheel `dist-info/licenses/` content from the exact artifacts shipped;
- preserve OpenVINO third-party programs notices applicable to the selected platform wheels;
- decide whether the model remains “fixed upstream revision + local conversion” or is hosted separately;
- if hosting converted model artifacts, add source, revision, transformation, hashes, declared license and
  attribution, and complete a separate redistribution review.

This draft is an engineering inventory, not legal advice.
