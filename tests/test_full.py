#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Raphaël Barrois

"""Full tests."""

import re
import unittest

import tdparser


class ArithmeticParserTestCase(unittest.TestCase):
    """Test parsing arithmetic expressions."""
    def setUp(self):

        class Integer(tdparser.Token):
            """A simple integer."""
            def __init__(self, text):
                super(Integer, self).__init__(text)
                self.value = int(text)

            def nud(self, context):
                """It evaluates to its (integer) value."""
                return self.value

        class Add(tdparser.Token):
            """Addition."""

            lbp = 10  # Precedence: higher than integers, lower than mult

            def led(self, left, context):
                """Evaluates to "left + <on the right up to next mult>"."""
                return left + context.expression(self.lbp)

        class Minus(tdparser.Token):
            lbp = 10

            def nud(self, context):
                """At the beginning of an expression, negates the expression."""
                return - context.expression(self.lbp)

            def led(self, left, context):
                """In the middle of an expression, computes "left - right"."""
                return left - context.expression(self.lbp)

        class Mult(tdparser.Token):
            lbp = 20  # Higher precedence than addition/substraction.

            def led(self, left, context):
                return left * context.expression(self.lbp)

        l = tdparser.Lexer(default_tokens=True)
        l.register_token(Integer, re.compile(r'[0-9]+'))
        l.register_token(Add, re.compile(r'\+'))
        l.register_token(Minus, re.compile(r'-'))
        l.register_token(Mult, re.compile(r'\*'))

        self.lexer = l

    def test_single_number(self):
        val = self.lexer.parse('13')
        self.assertEqual(13, val)

    def test_negative_number(self):
        val = self.lexer.parse('-13')
        self.assertEqual(-13, val)
        self.assertEqual(13, self.lexer.parse('--13'))
        self.assertEqual(13, self.lexer.parse('----13'))

    def test_simple_mult(self):
        self.assertEqual(8, self.lexer.parse('2 * 4'))
        self.assertEqual(8, self.lexer.parse('2 * 2 * 2'))
        self.assertEqual(8, self.lexer.parse('2 * (2 * 2)'))
        self.assertEqual(8, self.lexer.parse('(2 * 2) * 2'))
        self.assertEqual(8, self.lexer.parse('(2 + 2) * 2'))

    def test_precedence(self):
        self.assertEqual(8, self.lexer.parse('2 * 3 + 2'))
        self.assertEqual(10, self.lexer.parse('2 * (3+2)'))

    def test_negative_mult(self):
        self.assertEqual(8, self.lexer.parse('-2 * - 4'))
        self.assertEqual(8, self.lexer.parse('-2 * - (2 + 2)'))
        self.assertEqual(8, self.lexer.parse('-2 * 2 * -2'))
        self.assertEqual(8, self.lexer.parse('--2 * -2 * -2'))
        self.assertEqual(8, self.lexer.parse('-(-2 * -2 * -2)'))


class ParenthesizedParserTestCase(unittest.TestCase):
    """Test lexing parenthesized expressions."""

    def setUp(self):

        class RightParen(tdparser.Token):
            """A right parenthesis"""
            pass

        class LeftParen(tdparser.Token):
            """A left parenthesis"""

            def nud(self, context):
                """Read the content of the (...) block."""

                # Contains parsed data.
                contents = []
                while not isinstance(context.current_token, RightParen):
                    contents.append(context.expression())

                next_token = context.consume(RightParen)
                return [self.text] + contents + [next_token.text]

        l = tdparser.Lexer(default_tokens=False)
        l.register_token(LeftParen, re.compile(r'\('))
        l.register_token(RightParen, re.compile(r'\)'))

        self.lexer = l

    def test_trivial(self):

        expr = self.lexer.parse('()')
        self.assertEqual(['(', ')'], expr)

    def test_reads_a_single_expression(self):
        expr = self.lexer.parse('()()')
        self.assertEqual(['(', ')'], expr)

    def test_nested(self):
        expr = self.lexer.parse('(())')
        self.assertEqual(['(', ['(', ')'], ')'], expr)

    def test_chained_nested(self):
        expr = self.lexer.parse('(()())')
        self.assertEqual(['(', ['(', ')'], ['(', ')'], ')'], expr)

    def test_complex(self):
        expr = self.lexer.parse('(((()())())()(()(())(()()()()())))')
        self.assertEqual(
            ['(',
                ['(',
                    ['(',
                        ['(', ')'],
                        ['(', ')'],
                    ')'],
                    ['(', ')'],
                ')'],
                ['(', ')'],
                ['(',
                    ['(', ')'],
                    ['(',
                        ['(', ')'],
                    ')'],
                    ['(',
                        ['(', ')'],
                        ['(', ')'],
                        ['(', ')'],
                        ['(', ')'],
                        ['(', ')'],
                    ')'],
                ')'],
            ')'], expr)
