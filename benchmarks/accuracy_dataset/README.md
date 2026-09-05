# Accuracy dataset

64 synthetic images across 32 languages, each with the exact text lines it was
rendered from. Used by `benchmarks/run_accuracy_benchmark.py` to measure
recognition quality per language.

## Provenance

These images and their expected text originate from the `accuracy_test/`
directory on `main`, produced by that revision's own generator. They were moved
here during the packaging work because they are the only fixtures in the
repository with ground truth attached, and they cover the Latin and Cyrillic
languages whose mapping was previously broken.

Two changes were made while moving them:

- Image references became file names relative to `images/`. The originals were
  absolute paths under `/root/lhy/paddleocr/...`, which only resolved on the
  machine that generated them.
- The `latin` entry was dropped. It is a recognition-model prefix rather than a
  language, so it is not a valid value for `language` in the API.

The one-off JSON and HTML run reports that accompanied them were not carried
over: they are dated artifacts of individual runs, not fixtures.

## Layout

```
accuracy_dataset/
  ground_truth.json      language -> images + expected text lines
  images/                70 JPEG files, 600x400
```

`ground_truth.json` covers 64 of the 70 images. The remaining 6 belong to
languages whose entries carried no expected text upstream, so they cannot be
scored; they are kept because they are still valid inputs for the throughput
scripts.

## Scoring

`exact` is the fraction of expected lines matched exactly after Unicode NFC
normalisation, case folding and whitespace collapsing. No accent or script
stripping is applied, which would otherwise flatter non-Latin scripts.

`cer` is the character error rate over the joined text, with spaces removed.
It is reported alongside `exact` because a single confusable character can drop
`exact` to 0 for a line that is otherwise correct. Russian is the standing
example: the recogniser returns Cyrillic `С` for the Latin `C` in "OCR", giving
`exact=0.80` but `cer=0.012`.

## Caveats

The text is synthetic and cleanly rendered, so these numbers are an upper bound.
They confirm a language is genuinely served end to end and catch regressions in
the language mapping; they are not representative of photographed documents,
skewed scans, handwriting or low-resolution input.
