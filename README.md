# ytclips

## Install

From repository root:

```bash
pip install -e .
```

## Run

Preferred module execution:

```bash
python -m core --url "https://www.youtube.com/watch?v=..."
```

Or via console script:

```bash
ytclips --url "https://www.youtube.com/watch?v=..."
```

## Notes

- Only HTTPS YouTube URLs are accepted (`youtube.com`, `youtu.be`).
- By default, `--output-dir` must stay inside current working directory.
- Use `--allow-outside-output-dir` only if you intentionally want output elsewhere.
