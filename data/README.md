# Speech Corpus Data Directory

This directory is the location for real speech corpus data used in ECGA-IDPRNG-A evaluation.

## TIMIT Acoustic-Phonetic Continuous Speech Corpus

The paper originally references evaluation on standard speech corpora such as **TIMIT**.
TIMIT is proprietary and licensed by the **Linguistic Data Consortium (LDC)**:
- **LDC Catalog No.**: `LDC93S1`
- **URL**: [https://catalog.ldc.upenn.edu/LDC93S1](https://catalog.ldc.upenn.edu/LDC93S1)

### Instructions for TIMIT License Holders
If you have an active LDC license and access to the TIMIT dataset:
1. Place the uncompressed TIMIT dataset under `data/timit/` (preserving standard `TRAIN/` and `TEST/` subdirectories with `.WAV` NIST SPHERE files and `.PHN`/`.WRD`/`.TXT` companions).
2. Re-run the corpus evaluation script:
   ```bash
   python scripts/run_corpus_evaluation.py
   ```
   The automatic detection system in `scripts/load_speech_corpus.py` will detect TIMIT, strip the 1024-byte NIST SPHERE headers, sample 24 utterances stratified across dialect regions `DR1`–`DR8`, and perform evaluation on genuine TIMIT speech.

## Open-Corpus Fallback Hierarchy
If `data/timit/` is not present, the evaluation system automatically falls back through open, CC-licensed corpora:
1. **LibriSpeech dev-clean** (CC-BY-4.0) via `torchaudio` / OpenSLR (`openslr.org/12`).
2. **Mozilla Common Voice** (CC0) via Hugging Face `datasets`.
3. **Procedural Open Speech Corpus** (Fallback for offline execution).

The system **never** fabricates a `"TIMIT"` source label unless real TIMIT files were detected and parsed from `data/timit/`.
