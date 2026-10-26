#!/usr/bin/env python3
"""Build an explicit allowlist release. No network upload or secrets."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def source_file(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or any(p in ('', '.', '..') for p in relative.split('/')) or '\\' in relative:
        raise ValueError(f'Invalid release path: {relative!r}')
    allowed = (
        relative.startswith('assets/')
        or relative.startswith('data/') and path.suffix == '.json'
        or relative.startswith('templates/') and path.suffix == '.gohtml'
        or relative.startswith(('autobiografie/', 'research/columns/')) and path.suffix == '.md'
    )
    if not allowed:
        raise ValueError(f'Path outside runtime allowlist: {relative}')
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f'Symlink in release source: {relative}')
    if not current.is_file():
        raise ValueError(f'Missing release file: {relative}')
    return current


def prepare(destination: Path, goos: str | None, goarch: str | None, search_manifest: Path | None = None):
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink() or not destination.parent.is_dir():
        raise ValueError('Destination must be a new directory with an existing parent')
    files = json.loads((ROOT / 'ops/go-release-files.json').read_text())
    if not isinstance(files, list) or not files or len(files) != len(set(files)):
        raise ValueError('Runtime allowlist must be a nonempty list without duplicates')
    sources = [(name, source_file(ROOT, name)) for name in files]
    env = os.environ.copy()
    env['CGO_ENABLED'] = '0'
    if goos: env['GOOS'] = goos
    if goarch: env['GOARCH'] = goarch
    # Publish only a complete package. A failed build removes its own temporary tree.
    with tempfile.TemporaryDirectory(prefix='.jackie-release-', dir=destination.parent) as temp:
        stage = Path(temp) / 'release'
        stage.mkdir(mode=0o755)
        for name, source in sources:
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            target.chmod(0o644)
        (stage / 'bin').mkdir()
        subprocess.run(['go', 'build', '-trimpath', '-buildvcs=false', '-ldflags=-s -w',
                        '-o', str(stage / 'bin/jackieleven'), './cmd/jackieleven'],
                       cwd=ROOT, env=env, check=True)
        (stage / 'bin/jackieleven').chmod(0o755)
        if search_manifest is not None:
            manifest = json.loads(search_manifest.read_text())
            version = manifest.get('content_version', '')
            if len(version) != 64 or any(c not in '0123456789abcdef' for c in version):
                raise ValueError('Invalid search content version')
            subprocess.run(['go', 'build', '-trimpath', '-buildvcs=false', '-ldflags=-s -w',
                            '-o', str(stage / 'bin/jackieleven-search'), './cmd/jackieleven-search'],
                           cwd=ROOT, env=env, check=True)
            (stage / 'bin/jackieleven-search').chmod(0o755)
            (stage / 'search-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
            (stage / 'search-manifest.json').chmod(0o644)
        target_platform = subprocess.check_output(['go', 'env', 'GOOS', 'GOARCH'], env=env, text=True).splitlines()
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT))
        (stage / 'build.json').write_text(json.dumps({'revision': revision, 'dirty': dirty,
            'goos': target_platform[0], 'goarch': target_platform[1]}, indent=2) + '\n')
        manifest = []
        for path in sorted(stage.rglob('*')):
            if path.is_file():
                manifest.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(stage).as_posix()}\n')
        (stage / 'release-manifest.sha256').write_text(''.join(manifest))
        if destination.exists() or destination.is_symlink():
            raise ValueError('Destination appeared during build; refusing to replace it')
        stage.rename(destination)
    print(f'{len(manifest)} files prepared: {destination}')
    print(f'Runtime: {destination}/bin/jackieleven -root {destination} -listen 127.0.0.1:8080')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--goos', choices=('linux', 'darwin'))
    parser.add_argument('--goarch', choices=('amd64', 'arm64'))
    parser.add_argument('--search-manifest', type=Path, help='Include search binary and immutable manifest in this release')
    args = parser.parse_args()
    prepare(args.destination, args.goos, args.goarch, args.search_manifest)
