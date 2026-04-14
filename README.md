# eml2md

Convert `.eml` files to Markdown. Handles multipart emails, HTML bodies, and complex Exchange/Outlook headers correctly.

## Install

```bash
pip install git+https://github.com/mat21mf/eml2md
```

Or locally:

```bash
pip install -e .
```

## Usage

```bash
eml2md input.eml              # produces input.md
eml2md input.eml output.md   # explicit output path
```

## Requirements

Python 3.10+, `markdownify`

## License

MIT
