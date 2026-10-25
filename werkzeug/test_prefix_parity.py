#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('prefix_parity', Path(__file__).with_name('prefix_parity.py'))
prefix_parity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prefix_parity)


class PrefixParityTest(unittest.TestCase):
    def test_only_mounted_root_url_is_stripped(self):
        violations = []
        self.assertEqual(prefix_parity.mounted_url('/jackieleven/de/ueber?q=1#x', '/jackieleven', 'href', violations), '/de/ueber?q=1#x')
        self.assertEqual(violations, [])
        self.assertEqual(prefix_parity.mounted_url('https://jackieleven.com/de/ueber', '/jackieleven', 'canonical', violations), 'https://jackieleven.com/de/ueber')
        self.assertEqual(prefix_parity.mounted_url('#kapitel', '/jackieleven', 'href', violations), '#kapitel')

    def test_unprefixed_internal_url_is_a_visible_failure(self):
        violations = []
        self.assertEqual(prefix_parity.mounted_url('/de/ueber', '/jackieleven', 'href', violations), '/de/ueber')
        self.assertEqual(violations[0]['reason'], 'root-relative URL is outside mount prefix')

    def test_candidate_normalizer_leaves_canonical_and_jsonld_untouched(self):
        expected = {'headers': {}, 'body': [
            ['open', 'a', [['href', '/de/ueber']]],
            ['open', 'link', [['href', 'https://jackieleven.com/de/ueber'], ['rel', 'canonical']]],
            ['open', 'div', [['data-alternativen', '{"de":"/de/zeitreise"}']]],
            ['jsonld', {'url': 'https://jackieleven.com/de/ueber'}],
        ]}
        candidate = {'headers': {'x-robots-tag': 'noindex'}, 'body': [
            ['open', 'a', [['href', '/jackieleven/de/ueber']]],
            ['open', 'link', [['href', 'https://jackieleven.com/de/ueber'], ['rel', 'canonical']]],
            ['open', 'div', [
                ['data-alternativen', '{"de":"/jackieleven/de/zeitreise"}'],
                ['data-canonical-alternativen', '{"de":"/de/zeitreise"}'],
            ]],
            ['jsonld', {'url': 'https://jackieleven.com/de/ueber'}],
        ]}
        normalized, violations, noindex, canonical_alternatives = prefix_parity.normalize_candidate(expected, candidate, '/jackieleven')
        self.assertTrue(noindex)
        self.assertEqual(canonical_alternatives, 1)
        self.assertEqual(violations, [])
        self.assertEqual(normalized['headers'], {})
        self.assertEqual(normalized['body'][0][2][0][1], '/de/ueber')
        self.assertEqual(normalized['body'][1][2][0][1], 'https://jackieleven.com/de/ueber')
        self.assertEqual(normalized['body'][2][2][0][1], '{"de":"/de/zeitreise"}')
        self.assertEqual(normalized['body'][3][1]['url'], 'https://jackieleven.com/de/ueber')

    def test_canonical_alternatives_are_required_and_must_equal_baseline(self):
        expected = {'headers': {}, 'body': [['open', 'div', [['data-alternativen', '{"de":"/de/zeitreise"}']]]]}
        missing = {'headers': {'x-robots-tag': 'noindex'}, 'body': [['open', 'div', [['data-alternativen', '{"de":"/jackieleven/de/zeitreise"}']]]]}
        _, violations, _, _ = prefix_parity.normalize_candidate(expected, missing, '/jackieleven')
        self.assertIn('lack immutable canonical alternatives', violations[0]['reason'])
        wrong = {'headers': {'x-robots-tag': 'noindex'}, 'body': [['open', 'div', [
            ['data-alternativen', '{"de":"/jackieleven/de/zeitreise"}'],
            ['data-canonical-alternativen', '{"de":"/jackieleven/de/zeitreise"}'],
        ]]]}
        _, violations, _, _ = prefix_parity.normalize_candidate(expected, wrong, '/jackieleven')
        self.assertIn('differ from immutable production alternatives', violations[0]['reason'])

    def test_css_relative_and_prefixed_root_urls_resolve_to_same_contract(self):
        reference = '@font-face{src:url("/assets/fonts/a.woff2?v=1")} .x{background:url(/assets/i.png)}'
        candidate = '@font-face{src:url("../fonts/a.woff2?v=2")} .x{background:url(/jackieleven/assets/i.png)}'
        left, _, _ = prefix_parity.normalize_css(reference, '/assets/css/site.css')
        right, violations, forms = prefix_parity.normalize_css(candidate, '/assets/css/site.css', '/jackieleven', True)
        self.assertEqual(left, right)
        self.assertEqual(violations, [])
        self.assertEqual([item['form'] for item in forms], ['relative', 'root-relative'])

    def test_css_url_escaping_mount_is_not_hidden(self):
        _, violations, _ = prefix_parity.normalize_css('a{src:url(../../../outside.woff2)}', '/assets/css/site.css', '/jackieleven', True)
        self.assertEqual(violations[0]['reason'], 'root-relative URL is outside mount prefix')

    def test_only_exact_known_javascript_mount_edit_is_reversible(self):
        mounted = (
            "    var element = uebersicht ? track : marken[i];\n"
            "    var alternativen = JSON.parse(element.dataset.alternativen);\n"
            "    var canonicalAlternativen = JSON.parse(element.dataset.canonicalAlternativen || element.dataset.alternativen);\n"
            "      var adressen = link.tagName === 'LINK' ? canonicalAlternativen : alternativen;\n"
            "      var ziel = adressen[link.getAttribute('hreflang')];"
        )
        normalized, transformations = prefix_parity.normalize_known_mount_javascript('/assets/js/zeitgraph.js', mounted)
        self.assertEqual(len(transformations), 2)
        self.assertIn("JSON.parse((uebersicht ? track : marken[i]).dataset.alternativen)", normalized)
        altered, transformations = prefix_parity.normalize_known_mount_javascript('/assets/js/zeitgraph.js', mounted + '\nmalicious()')
        self.assertEqual(len(transformations), 2)
        self.assertTrue(altered.endswith('malicious()'))

    def test_prefix_validation(self):
        self.assertEqual(prefix_parity.clean_prefix('/jackieleven/'), '/jackieleven')
        for invalid in ('', '/', 'jackieleven', '//jackieleven', '/a//b', '/a/../b'):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    prefix_parity.clean_prefix(invalid)


if __name__ == '__main__':
    unittest.main()
