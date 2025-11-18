#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_translate_and_compile_ts.py

Usage (PowerShell / cmd):
  python generate_translate_and_compile_ts.py --code-dir . --out-dir i18n --base-name kat_overlap --translate --compile

What it does:
 1. Extracte toutes les chaînes FR depuis les .py (tr(), self.tr(), QCoreApplication.translate()).
 2. Crée 3 fichiers .ts nouveaux: kat_overlap_fr.new.ts, kat_overlap_en.new.ts, kat_overlap_es.new.ts.
    - FR: translation = source (les textes sont en français et sont copiés).
    - EN/ES:
        - si --translate et googletrans installé: effectue traduction automatique et place le texte traduit (sans type="unfinished").
        - sinon: laisse <translation type="unfinished"/> (vide) et exporte CSV prêt à traduire.
 3. (option) Si --compile est passé et lrelease est disponible, exécute lrelease pour produire .qm.
 4. Crée backups des .ts existants (si présents) en .bak.TIMESTAMP avant d'écrire.

Notes:
 - Pour la traduction automatique, installe: pip install googletrans==4.0.0-rc1
 - Le script essaie d'être prudent: n'écrase pas les anciens .ts sans backup.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import argparse, time, shutil, subprocess, csv, sys

# extraction regexes
TR_CALL_RE = re.compile(r'(\bQCoreApplication\.translate\(|\btr\(|\.tr\()')
STRING_LITERAL_RE = re.compile(r'(?P<quote>[\'"])(?P<s>(?:\\.|(?!\1).)*)\1', re.DOTALL)
CLASS_DEF_RE = re.compile(r'^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)', re.MULTILINE)

def extract_code_strings(code_dir: Path):
    ctx_map = {}
    for p in code_dir.rglob('*.py'):
        if any(part in ('venv','env','__pycache__') or part.startswith('.') for part in p.parts):
            continue
        try:
            text = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        classes = []
        for m in CLASS_DEF_RE.finditer(text):
            classes.append((m.start(), m.group(1)))
        for m in TR_CALL_RE.finditer(text):
            start = m.start()
            tail = text[start:start+1200]
            found = STRING_LITERAL_RE.findall(tail)
            if tail.strip().startswith('QCoreApplication.translate'):
                if len(found) >= 2:
                    s = found[1][1]
                else:
                    continue
            else:
                if found:
                    s = found[0][1]
                else:
                    continue
            try:
                s = bytes(s, "utf-8").decode("unicode_escape")
            except Exception:
                pass
            ctx = '@default'
            last_pos = -1
            for pos,name in classes:
                if pos <= start and pos > last_pos:
                    last_pos = pos
                    ctx = name
            ctx_map.setdefault(ctx, set()).add(s)
    return ctx_map

def backup_if_exists(p: Path):
    if p.exists():
        bak = p.with_suffix(p.suffix + f'.bak.{time.strftime("%Y%m%dT%H%M%S")}')
        shutil.copy2(p, bak)
        print(f"[backup] {p} -> {bak}")

def write_ts(path: Path, ctx_map, language=None, translations_map=None, mark_unfinished=False):
    """
    translations_map: dict (context->source->translation) or None
    mark_unfinished: if True and no translation provided, set type="unfinished"
    """
    TS = ET.Element('TS'); TS.set('version','2.1')
    if language:
        TS.set('language', language)
    for ctx_name, sources in sorted(ctx_map.items()):
        ctx = ET.Element('context')
        name = ET.Element('name'); name.text = ctx_name
        ctx.append(name)
        for s in sorted(sources):
            msg = ET.Element('message')
            src = ET.Element('source'); src.text = s
            msg.append(src)
            tr = ET.Element('translation')
            transl = None
            if translations_map:
                transl = translations_map.get(ctx_name, {}).get(s)
            if transl is not None:
                tr.text = transl
            else:
                if mark_unfinished:
                    tr.set('type','unfinished')
            msg.append(tr)
            ctx.append(msg)
        TS.append(ctx)
    tree = ET.ElementTree(TS)
    tree.write(path, encoding='utf-8', xml_declaration=True)

def try_import_googletrans():
    try:
        from googletrans import Translator
        return Translator()
    except Exception:
        return None

def translate_bulk(translator, texts, dest):
    # translator from googletrans: will accept list of strings
    # return list of translated strings same order
    if translator is None:
        raise RuntimeError("googletrans translator is None")
    # googletrans translator.translate accepts list
    res = translator.translate(texts, dest=dest)
    # when single string, googletrans may return single object
    if not isinstance(res, list):
        res = [res]
    return [r.text for r in res]

def export_untranslated_csv(csv_path: Path, ctx_map):
    rows = []
    for ctx, sources in sorted(ctx_map.items()):
        for s in sorted(sources):
            rows.append([s, ctx, ''])
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['source','context','translation'])
        w.writerows(rows)
    print(f"[csv] Wrote {csv_path} ({len(rows)} rows)")

def run_lrelease(ts_paths, out_dir):
    # find lrelease on PATH
    cmd = ['lrelease'] + [str(p) for p in ts_paths]
    try:
        print("[lrelease] Running:", ' '.join(cmd))
        completed = subprocess.run(cmd, cwd=out_dir, capture_output=True, text=True)
        if completed.returncode == 0:
            print("[lrelease] Success")
            return True, completed.stdout
        else:
            print("[lrelease] Failed: rc", completed.returncode)
            print(completed.stdout)
            print(completed.stderr)
            return False, completed.stderr or completed.stdout
    except FileNotFoundError:
        print("[lrelease] Not found on PATH. Skipping compilation.")
        return False, "lrelease-not-found"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--code-dir', required=True)
    ap.add_argument('--out-dir', default='i18n')
    ap.add_argument('--base-name', default='kat_overlap')
    ap.add_argument('--translate', action='store_true', help='attempt automatic translation via googletrans')
    ap.add_argument('--compile', action='store_true', help='run lrelease to produce .qm (requires lrelease on PATH)')
    ap.add_argument('--mark-fr-unfinished', action='store_true', help='mark FR translations as unfinished instead of copying source text')
    args = ap.parse_args()

    code_dir = Path(args.code_dir)
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    print("Extracting strings from code...")
    ctx_map = extract_code_strings(code_dir)
    total = sum(len(v) for v in ctx_map.values())
    print(f"  {total} strings across {len(ctx_map)} contexts")

    # prepare paths
    fr_new = out_dir / (args.base_name + '_fr.new.ts')
    en_new = out_dir / (args.base_name + '_en.new.ts')
    es_new = out_dir / (args.base_name + '_es.new.ts')
    # backup originals if present (non-new)
    for p in (out_dir / (args.base_name + '_fr.ts'),
              out_dir / (args.base_name + '_en.ts'),
              out_dir / (args.base_name + '_es.ts')):
        backup_if_exists(p)

    # translations maps
    en_map = {}
    es_map = {}

    if args.translate:
        print("Attempting automatic translation with googletrans...")
        translator = try_import_googletrans()
        if translator is None:
            print("[warn] googletrans not installed or import failed. Skipping automatic translation.")
            args.translate = False
        else:
            # build list of texts and contexts aligned
            texts = []
            keys = []
            for ctx, sources in sorted(ctx_map.items()):
                for s in sorted(sources):
                    texts.append(s)
                    keys.append((ctx, s))
            # chunk if large (googletrans may accept lists but to be safe chunk by 100)
            def chunks(lst, n):
                for i in range(0, len(lst), n):
                    yield lst[i:i+n], i
            print(f"Translating {len(texts)} strings to en and es (chunks)...")
            for chunk, offset in chunks(texts, 100):
                try:
                    tr_en = translate_bulk(translator, chunk, dest='en')
                    tr_es = translate_bulk(translator, chunk, dest='es')
                except Exception as e:
                    print("[translate error]", e)
                    args.translate = False
                    break
                for i, (te, ts) in enumerate(zip(tr_en, tr_es)):
                    ctx, src = keys[offset + i]
                    en_map.setdefault(ctx, {})[src] = te
                    es_map.setdefault(ctx, {})[src] = ts
            if args.translate:
                print("[translate] Automatic translation finished.")
    # If translation not performed, we will leave en_map/es_map empty and write unfinished tags + export CSV for manual translation
    if not args.translate:
        csv_en = out_dir / (args.base_name + '_to_translate_en.csv')
        csv_es = out_dir / (args.base_name + '_to_translate_es.csv')
        export_untranslated_csv(csv_en, ctx_map)
        export_untranslated_csv(csv_es, ctx_map)
        mark_unfinished = True
    else:
        mark_unfinished = False

    # Write FR (copy source unless mark-fr-unfinished)
    fr_map = None
    if args.mark_fr_unfinished:
        write_ts(fr_new, ctx_map, language='fr', translations_map=None, mark_unfinished=True)
    else:
        # translations_map for fr is just copy
        fr_map = {}
        for ctx, sources in ctx_map.items():
            fr_map[ctx] = {s: s for s in sources}
        write_ts(fr_new, ctx_map, language='fr', translations_map=fr_map, mark_unfinished=False)
    print("[write] FR ->", fr_new)

    # Write EN/ES
    write_ts(en_new, ctx_map, language='en', translations_map=en_map if en_map else None, mark_unfinished=mark_unfinished)
    write_ts(es_new, ctx_map, language='es', translations_map=es_map if es_map else None, mark_unfinished=mark_unfinished)
    print("[write] EN ->", en_new)
    print("[write] ES ->", es_new)

    # Optionally compile to .qm
    if args.compile:
        # compile the .new.ts files into .qm (output into same out_dir)
        ok, out = run_lrelease([fr_new, en_new, es_new], out_dir)
        if ok:
            print("[compile] .qm files generated in", out_dir)
        else:
            print("[compile] Failed or skipped; ensure lrelease is installed and on PATH.")
    print("Done. Inspect the .new.ts files with Qt Linguist, then rename to replace originals when ready.")

if __name__ == '__main__':
    main()
