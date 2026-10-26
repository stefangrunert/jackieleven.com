#!/usr/bin/env python3
"""Read-only verifier of the phase-1 source inventory; not an importer."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import yaml


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode('utf-8')).hexdigest()


def pointer(value, path):
    for key in path.strip('/').split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path(__file__).with_name('pilot-manifest.json'))
    parser.add_argument('--website-root', type=Path, required=True)
    parser.add_argument('--archive-root', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    roots = {'website': args.website_root, 'archive': args.archive_root}
    inputs = manifest['inputs']
    content = {}

    def git(repo, *argv):
        return subprocess.check_output(['git', *argv], cwd=roots[repo])

    for repo, data in manifest['repositories'].items():
        actual = git(repo, 'rev-parse', data['commit'] + '^{commit}').decode().strip()
        require(actual == data['commit'], 'Commit mismatch: ' + repo)
    for key, entry in inputs.items():
        repo, path = entry['repository'], entry['path']
        require(not Path(path).is_absolute() and '..' not in Path(path).parts, 'Unsafe input path')
        ref = manifest['repositories'][repo]['commit'] + ':' + path
        raw = git(repo, 'show', ref)
        require(digest(raw) == entry['sha256'], 'File SHA mismatch: ' + key)
        require(git(repo, 'rev-parse', ref).decode().strip() == entry['git_blob'], 'Git blob mismatch: ' + key)
        content[key] = raw
    catalog = json.loads(content['website:data/quellen.json'])
    columns = json.loads(content['website:data/kolumnen.json'])['dateien']
    languages = {lang: json.loads(content['website:data/lang/' + lang + '.json']) for lang in ['de', 'en']}
    passage_ids = set()
    pilot_ids = set()
    total_evidence = 0
    matched = 0
    statements = set()
    for document in manifest['documents']:
        pid = document['pilot_id']
        require(pid not in pilot_ids, 'Duplicate pilot id')
        pilot_ids.add(pid)
        require(document['passage_anchor_status'] == 'not_implemented', 'Unexpected anchor assertion')
        did = document['archive_entity_id'] or document['proposed_archive_entity_id']
        q = None
        if document['archive_entity_id']:
            entity = yaml.safe_load(content[document['archive_record']])
            require(entity['id'] == did, 'Archive document mismatch: ' + pid)
            require(entity['language'] == document['original_language'], 'Original language mismatch')
            q = pointer(catalog, document['website_record_pointer'])
            require(q['id'] == document['website_source_id'], 'Website identity mismatch: ' + pid)
            require(q['url'].split('#')[0] == entity['url'].split('#')[0], 'Source URL mapping mismatch')
            has_page = q['stufe'] != 'weitere'
            require(has_page == (document['target_kind'] == 'detail_page'), 'Detail target mismatch')
            for lang in ['de', 'en']:
                base = '/' + lang + '/' + languages[lang]['pfad.stimmen']
                expected = base + '/' + q['id'] if has_page else base + '?auswahl=0#' + q['id']
                require(expected == document['website_targets'][lang], 'Route mismatch: ' + pid)
            if not has_page:
                require(not document['text_units'], 'Metadata control must not have passages')
        else:
            source = inputs[document['research_source']]['path']
            require(Path(source).name in columns, 'Column absent from allowlist')
            require(document['archive_entity_status'] == 'proposal_only_not_in_archive', 'Proposed identity not marked')
            # Read-only existence probe against the pinned tree, not the working copy.
            exists = subprocess.run(['git', 'cat-file', '-e', manifest['repositories']['archive']['commit'] + ':data/' + did + '.yaml'], cwd=roots['archive'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
            require(not exists, 'Proposed identity already exists')
            slug = Path(source).stem.replace('_', '-')
            for lang in ['de', 'en']:
                require(document['website_targets'][lang] == '/' + lang + '/' + languages[lang]['pfad.pool'] + '/' + slug, 'Column route mismatch')
        texts = {}
        for unit in document['text_units']:
            uid = unit['proposed_passage_ref']
            require(uid.startswith(did + '#p-') and uid not in passage_ids, 'Invalid/duplicate passage id')
            passage_ids.add(uid)
            selector = unit['selector']
            raw = content[selector['input']]
            if 'json_pointer' in selector:
                text = pointer(json.loads(raw), selector['json_pointer'])
                require(selector['record_id'] == q['id'], 'Text selector identity mismatch')
            else:
                text = '\n'.join(raw.decode().splitlines()[selector['line_start'] - 1:selector['line_end']])
            require(isinstance(text, str) and digest(text) == unit['raw_text_sha256'], 'Text SHA mismatch: ' + uid)
            if unit['text_kind'] == 'summary':
                require(unit['text_voice'] == 'editorial' and unit['language'] in ['de', 'en'], 'Summary attribution mismatch')
            if unit['text_kind'] == 'original':
                require(unit['language'] == document['original_language'], 'Original passage language mismatch')
                require(unit['text_voice'] == document['source_voice'], 'Original voice mismatch')
            texts[uid] = text
        for sample in document['evidence_samples']:
            total_evidence += 1
            entity = yaml.safe_load(content[sample['input']])
            require(entity['id'] == sample['subject'], 'Evidence subject mismatch')
            statement = next(s for s in entity[sample['predicate']] if s['statement_id'] == sample['statement_id'])
            statements.add(sample['statement_id'])
            reference = statement['references'][sample['reference_index']]
            require(reference['document'] == did, 'Evidence source mismatch')
            require(reference.get('evidence_type') == sample['evidence_type'], 'Evidence type mismatch')
            require(reference.get('locator') == sample['locator'], 'Evidence locator mismatch')
            require({k: v for k, v in statement.items() if k.endswith('_value')} == sample['value'], 'Statement value mismatch')
            require(statement.get('rank', 'normal') == sample['rank'] and statement.get('certainty') == sample['certainty'], 'Rank/certainty mismatch')
            quote = reference.get('quote')
            require((digest(quote) if quote else None) == sample['quote_sha256'], 'Quote SHA mismatch')
            require(reference.get('passage') == sample['passage_ref_in_archive'], 'Archive passage mismatch')
            require(sample['passage_binding_status'] == 'unbound', 'Unreviewed passage claimed as bound')
            for uid in sample['candidate_passage_refs']:
                require(quote and quote in texts[uid], 'Candidate quote mismatch')
            if sample['candidate_passage_refs']:
                matched += 1
    require(len(pilot_ids) == 16 and len(passage_ids) == 119, 'Pilot membership changed')
    # Existing templates do not yet render the proposed paragraph anchors.
    for key in ['website:templates/quelle.gohtml', 'website:templates/kolumne.gohtml']:
        require(b'id="p-' not in content[key], 'Recheck newly introduced anchors')
    print(f'OK: {len(inputs)} file hashes; {len(pilot_ids)} documents; {len(passage_ids)} text selectors; {total_evidence} evidence references / {len(statements)} statements; {matched} exact quote candidates.')


if __name__ == '__main__':
    main()
