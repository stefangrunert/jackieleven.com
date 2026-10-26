"""DeepInfra OpenAI-compatible embeddings; network used only with explicit --embed."""
import json
import math
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

PROFILE_NAME = 'qwen3-8b-1024-v1'
QUERY_INSTRUCTION = 'Given a question about the Scottish songwriter Jackie Leven, retrieve passages from his own writing, press coverage, concert history and discography that answer it'
PROFILE = {'id': PROFILE_NAME, 'provider': 'deepinfra', 'model': 'Qwen/Qwen3-Embedding-8B',
           'provider_revision': 'mutable-provider-model-alias', 'native_dimensions': 4096,
           'dimensions': 1024, 'normalization': 'truncate-then-l2', 'document_input': 'text',
           'query_instruction': QUERY_INSTRUCTION, 'encoding_format': 'float',
           'endpoint': 'https://api.deepinfra.com/v1/openai/embeddings'}


class ProviderError(RuntimeError):
    pass


def normalize(vector, native=4096):
    if not isinstance(vector, list) or len(vector) != native:
        raise ProviderError('embedding_dimension_mismatch')
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in vector):
        raise ProviderError('embedding_nonfinite')
    result = [float(x) for x in vector[:1024]]
    norm = math.sqrt(sum(x*x for x in result))
    if norm <= 0 or not math.isfinite(norm):
        raise ProviderError('embedding_zero_norm')
    return [x/norm for x in result]


def load_key(key_file=None):
    # Called by the importer only when --embed is explicit. Never print this value/path.
    value = os.environ.get('JACKIE_DEEPINFRA_API_KEY', '')
    key_file = key_file or os.environ.get('JACKIE_DEEPINFRA_API_KEY_FILE')
    if not value and key_file:
        value = Path(key_file).read_text().strip()
    if not value or '\n' in value or '\r' in value:
        raise ProviderError('provider_key_unavailable')
    return value


class DeepInfra:
    def __init__(self, key, opener=None, sleep=time.sleep, timeout=30, retries=2):
        self.key, self.opener, self.sleep = key, opener or urllib.request.urlopen, sleep
        self.timeout, self.retries = min(max(timeout, 1), 60), min(max(retries, 0), 3)

    def embed(self, texts):
        if not 1 <= len(texts) <= 16 or any(not t or len(t) > 2400 for t in texts):
            raise ProviderError('embedding_batch_limit')
        data = json.dumps({'model': PROFILE['model'], 'input': texts, 'encoding_format': 'float'}).encode()
        request = urllib.request.Request(PROFILE['endpoint'], data=data, headers={
            'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.key}, method='POST')
        for attempt in range(self.retries + 1):
            try:
                with self.opener(request, timeout=self.timeout) as response:
                    raw = response.read(8*1024*1024 + 1)
                if len(raw) > 8*1024*1024:
                    raise ProviderError('provider_response_limit')
                result = json.loads(raw)
                rows = result['data']
                if len(rows) != len(texts) or sorted(r['index'] for r in rows) != list(range(len(texts))):
                    raise ProviderError('embedding_batch_mismatch')
                return [normalize(r['embedding']) for r in sorted(rows, key=lambda r: r['index'])]
            except urllib.error.HTTPError as exc:
                retry = exc.code in (408, 429, 500, 502, 503, 504)
                exc.close()
                if not retry or attempt == self.retries:
                    raise ProviderError('provider_http_error') from None
            except (urllib.error.URLError, TimeoutError, OSError):
                if attempt == self.retries:
                    raise ProviderError('provider_unavailable') from None
            except (ValueError, KeyError, TypeError):
                raise ProviderError('provider_invalid_response') from None
            self.sleep(min(2**attempt, 4))
