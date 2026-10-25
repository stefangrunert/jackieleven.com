#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('parity', Path(__file__).with_name('parity.py'))
parity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parity)


def contract(markup):
    parser = parity.HTMLContract()
    parser.feed(markup)
    parser.close()
    return parser.events, parser.inline_text


class HTMLContractTest(unittest.TestCase):
    def test_inline_boundary_space_is_not_discarded(self):
        spaced = contract('<p>Hello <em>x</em> world</p>')
        joined = contract('<p>Hello<em>x</em>world</p>')
        self.assertEqual(spaced[0], joined[0], 'structural contract deliberately collapses indentation')
        self.assertNotEqual(spaced[1], joined[1])
        self.assertEqual(spaced[1], [['p', ['Hello x world']]])
        self.assertEqual(joined[1], [['p', ['Helloxworld']]])

    def test_whitespace_between_inline_siblings_is_visible(self):
        spaced = contract('<p><span>A</span> <span>B</span></p>')
        joined = contract('<p><span>A</span><span>B</span></p>')
        self.assertEqual(spaced[1], [['p', ['A B']]])
        self.assertEqual(joined[1], [['p', ['AB']]])

    def test_equivalent_collapsible_inline_whitespace_is_equal(self):
        plain = contract('<p>A <strong>B</strong> C</p>')
        formatted = contract('<p>A\n\t<strong>B</strong>\r\n C</p>')
        self.assertEqual(plain, formatted)

    def test_block_indentation_is_not_rendered_as_inline_space(self):
        compact = contract('<main><p>A</p><p>B</p></main>')
        pretty = contract('<main>\n  <p>A</p>\n  <p>B</p>\n</main>')
        self.assertEqual(compact, pretty)


    def test_nbsp_is_not_collapsed_to_an_ascii_space(self):
        ordinary = contract('<p>A B</p>')
        nonbreaking = contract('<p>A&nbsp;B</p>')
        self.assertNotEqual(ordinary[0], nonbreaking[0])
        self.assertEqual(nonbreaking[0][1], ['text', 'A\u00a0B'])

    def test_v1_baseline_remains_readable_but_v2_compares_inline_text(self):
        expected_v1 = {'status':200, 'headers':{}, 'body':[['text','AB']]}
        actual = {**expected_v1, 'inline_text':[['p',['A B']]]}
        self.assertEqual(parity.diff_result(expected_v1, actual), [])
        expected_v2 = {**expected_v1, 'inline_text':[['p',['AB']]]}
        self.assertEqual(parity.diff_result(expected_v2, actual)[0]['field'], 'inline_text')
        self.assertIn('--- PHP', ''.join(parity.diff_result(expected_v2, actual)[0]['diff']))

    def test_known_json_data_attributes_compare_as_structured_json(self):
        php = {'status':200, 'headers':{}, 'body':[
            ['open','div',[['data-seo','{"titel":"F\\u00fcr","url":"https:\\/\\/example.test"}']]],
        ]}
        go = {'status':200, 'headers':{}, 'body':[
            ['open','div',[['data-seo','{"url":"https://example.test","titel":"Für"}']]],
        ]}
        self.assertEqual(parity.diff_result(php, go), [])

    def test_json_data_attribute_array_order_remains_significant(self):
        left = {'status':200, 'headers':{}, 'body':[['open','div',[['data-seo','[1,2]']]]]}
        right = {'status':200, 'headers':{}, 'body':[['open','div',[['data-seo','[2,1]']]]]}
        self.assertEqual(parity.diff_result(left, right)[0]['field'], 'body')

    def test_encoded_slash_contract_checks_safe_status_not_server_error_html(self):
        apache = {'status':404, 'headers':{'content-type':'text/html; charset=iso-8859-1'}, 'body':[['text','Not Found']]}
        app = {'status':404, 'headers':{'content-type':'text/html; charset=utf-8'}, 'body':[['text','Hier ist nichts']]}
        self.assertEqual(parity.diff_result(apache, app, {'path':'/de%2Fueber'}), [])
        leaked = {**app, 'body':[['text','panic: /Users/stefan/secret']]}
        self.assertEqual(parity.diff_result(apache, leaked, {'path':'/de%2Fueber'})[0]['field'], 'body-leak')
        finding = parity.infrastructure_check(apache, app, {'path':'/de%2Fueber'})
        self.assertFalse(finding['body_parity_compared'])
        self.assertTrue(finding['no_leak'])


if __name__ == '__main__':
    unittest.main()
