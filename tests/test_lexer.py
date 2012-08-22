#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Raphaël Barrois

"""Tests for lexer-related code."""

import re
from .compat import unittest

import tdparser
from tdparser import lexer as tdparser_lexer


class BaseLexerTestCase(unittest.TestCase):
    """Tests base functions of the Lexer class."""

    def test_with_parens(self):
        lexer = tdparser.Lexer(with_parens=True)
        self.assertEqual(2, len(lexer.tokens._tokens))
        self.assertEqual([tdparser.LeftParen, tdparser.RightParen],
            [token_class for token_class, _token_re in lexer.tokens._tokens])

    def test_no_with_parens(self):
        lexer = tdparser.Lexer(with_parens=False)
        self.assertEqual(0, len(lexer.tokens._tokens))


class TokenRegistryTestCase(unittest.TestCase):

    def test_add_token(self):
        class AToken(tdparser.Token):
            pass

        class BToken(tdparser.Token):
            pass

        registry = tdparser_lexer.TokenRegistry()
        self.assertEqual(0, len(registry._tokens))

        a_re = re.compile(r'a+')
        b_re = re.compile(r'b+')

        registry.register(AToken, a_re)
        self.assertEqual(1, len(registry._tokens))
        self.assertEqual([(AToken, a_re)], registry._tokens)

        registry.register(BToken, b_re)
        self.assertEqual(2, len(registry._tokens))
        self.assertEqual((BToken, b_re), registry._tokens[1])

    def test_dual_registration(self):
        class AToken(tdparser.Token):
            pass

        registry = tdparser_lexer.TokenRegistry()
        self.assertEqual(0, len(registry._tokens))

        a_re = re.compile(r'a+')
        b_re = re.compile(r'b+')

        registry.register(AToken, a_re)
        self.assertEqual(1, len(registry._tokens))
        self.assertEqual([(AToken, a_re)], registry._tokens)

        registry.register(AToken, b_re)
        self.assertEqual(2, len(registry._tokens))
        self.assertEqual((AToken, b_re), registry._tokens[1])

    def test_get_matches_no_tokens_notext(self):
        registry = tdparser_lexer.TokenRegistry()
        self.assertEqual([], list(registry.matching_tokens('')))

    def test_get_matches_no_tokens_text(self):
        registry = tdparser_lexer.TokenRegistry()
        self.assertEqual([], list(registry.matching_tokens('foo')))

    def test_get_matches_notext(self):
        registry = tdparser_lexer.TokenRegistry()
        registry.register(tdparser.Token, re.compile(r'a'))
        self.assertEqual([], list(registry.matching_tokens('')))

    def test_get_matches(self):
        registry = tdparser_lexer.TokenRegistry()
        registry.register(tdparser.Token, re.compile(r'a'))

        matches = list(registry.matching_tokens('aaa'))
        self.assertEqual(1, len(matches))
        self.assertEqual(tdparser.Token, matches[0][0])

    def test_multiple_matches(self):
        class AToken(tdparser.Token):
            pass

        class AAToken(tdparser.Token):
            pass

        registry = tdparser_lexer.TokenRegistry()
        registry.register(AToken, re.compile(r'a'))
        registry.register(AAToken, re.compile(r'aa'))

        matches = list(registry.matching_tokens('aaa'))
        self.assertEqual(2, len(matches))
        self.assertEqual(AToken, matches[0][0])
        self.assertEqual(AAToken, matches[1][0])

    def test_get_token_multiple(self):
        class AToken(tdparser.Token):
            pass

        class AAToken(tdparser.Token):
            pass

        registry = tdparser_lexer.TokenRegistry()
        registry.register(AToken, re.compile(r'a'))
        registry.register(AAToken, re.compile(r'aa'))

        match = registry.get_token('aaa')
        self.assertEqual(AAToken, match[0])

    def test_get_token_multiple_inverted(self):
        class AToken(tdparser.Token):
            pass

        class AAToken(tdparser.Token):
            pass

        registry = tdparser_lexer.TokenRegistry()
        registry.register(AAToken, re.compile(r'aa'))
        registry.register(AToken, re.compile(r'a'))

        match = registry.get_token('aaa')
        self.assertEqual(AAToken, match[0])


class GetTokenTestCase(unittest.TestCase):

    def test_get_token_no_text(self):
        lexer = tdparser.Lexer(with_parens=True)
        token_class, re_match = lexer.tokens.get_token('')
        self.assertIsNone(token_class)
        self.assertIsNone(re_match)

    def test_get_token_no_text_no_tokens(self):
        lexer = tdparser.Lexer(with_parens=False)
        token_class, re_match = lexer.tokens.get_token('')
        self.assertIsNone(token_class)
        self.assertIsNone(re_match)

    def test_get_token_unmatched(self):
        lexer = tdparser.Lexer(with_parens=True)
        token_class, re_match = lexer.tokens.get_token('aaa')
        self.assertIsNone(token_class)
        self.assertIsNone(re_match)

    def test_get_token_no_tokens(self):
        lexer = tdparser.Lexer(with_parens=False)
        token_class, re_match = lexer.tokens.get_token('aaa')
        self.assertIsNone(token_class)
        self.assertIsNone(re_match)

    def test_get_token(self):
        lexer = tdparser.Lexer(with_parens=True)
        token_class, re_match = lexer.tokens.get_token('(((')
        self.assertEqual(tdparser.LeftParen, token_class)
        self.assertIsNotNone(re_match)

    def test_get_token_picks_first(self):
        lexer = tdparser.Lexer(with_parens=True)
        token_class, re_match = lexer.tokens.get_token('aa(((')
        self.assertIsNone(token_class)
        self.assertIsNone(re_match)

    def test_get_token_scans_all_possible_tokens(self):
        lexer = tdparser.Lexer(with_parens=True)
        token_class, re_match = lexer.tokens.get_token(')(')
        self.assertEqual(tdparser.RightParen, token_class)
        self.assertIsNotNone(re_match)

    def test_longest_match(self):
        lexer = tdparser.Lexer(with_parens=False)
        class AToken(tdparser.Token):
            pass

        class BToken(tdparser.Token):
            pass

        lexer.register_token(AToken, re.compile(r'a'))
        lexer.register_token(BToken, re.compile(r'aa'))

        token_class, match = lexer.tokens.get_token('aaa')
        self.assertEqual(BToken, token_class)


class LexTestCase(unittest.TestCase):

    def test_lex_empty(self):
        lexer = tdparser.Lexer()
        tokens = list(lexer.lex(''))
        self.assertEqual(1, len(tokens))
        self.assertEqual(tdparser.EndToken, tokens[0].__class__)

    def test_lex_tokens(self):
        text = '((((((()()()))))))((((((('
        lexer = tdparser.Lexer(with_parens=True)
        tokens = list(lexer.lex(text))
        self.assertEqual(1 + len(text), len(tokens))
        for i, token in enumerate(tokens[:-1]):
            self.assertEqual(text[i], token.text)
            if token.text == '(':
                self.assertEqual(tdparser.LeftParen, token.__class__)
            else:
                self.assertEqual(tdparser.RightParen, token.__class__)
        self.assertEqual(tdparser.EndToken, tokens[-1].__class__)

    def test_lex_skips_blank(self):
        lexer = tdparser.Lexer(with_parens=True)
        tokens = list(lexer.lex('  ('))
        self.assertEqual(2, len(tokens))
        self.assertEqual('(', tokens[0].text)
        self.assertEqual(tdparser.LeftParen, tokens[0].__class__)
        self.assertEqual(tdparser.EndToken, tokens[-1].__class__)

    def test_lex_custom_blank_chars(self):
        lexer = tdparser.Lexer(with_parens=True, blank_chars=('a', ' '))
        tokens = list(lexer.lex(' a('))
        self.assertEqual(2, len(tokens))
        self.assertEqual('(', tokens[0].text)
        self.assertEqual(tdparser.LeftParen, tokens[0].__class__)
        self.assertEqual(tdparser.EndToken, tokens[-1].__class__)

    def test_lex_invalid_char(self):
        lexer = tdparser.Lexer(with_parens=False)
        with self.assertRaises(ValueError):
            list(lexer.lex('foo'))
