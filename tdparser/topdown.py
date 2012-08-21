# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Raphaël Barrois

"""Basic implementation of top-down operator precedence.

In order to use it for parsing:
- Define tokens derivating from the Token class
- Subclass the Lexer class and replace or extend its TOKENS attribute
- Call MyLexer(my_text).parse()
"""

from __future__ import unicode_literals

import re


class ParserError(Exception):
    pass


class ParserSyntaxError(ParserError):
    pass


class Token(object):
    """Base class for tokens.

    Ref:
        http://effbot.org/zone/simple-top-down-parsing.htm
        http://javascript.crockford.com/tdop/tdop.html
    """

    # Left binding power
    # Controls how much this token binds to a token on its right
    lbp = 0

    def __init__(self, text=''):
        self.text = text

    def __repr__(self):
        return "<%s: %r>" % (self.__class__.__name__, self.text)

    def nud(self, context):
        """Null denotation.

        Describes what happens to this token when located at the beginning of
        an expression.

        Args:
            context (Parser): the parser from which next tokens/subexpressions
                can be retrieved

        Returns:
            object: Parsed value for this token (a node, a value, ...)
        """
        raise ParserSyntaxError(
            "Unexpected token %s at the left of an expression (pos: %d)" % (
            self, context.current_pos))

    def led(self, left, context):
        """Left denotation.

        Describe what happens to this token when appearing inside a construct
        (at the left of the rest of the construct).

        Args:
            context (Parser): the parser from which 'next' data can be
                retrieved
            left (object): the representation of the construct on the
                left of this token

        Returns:
            object built from this token, what is on its right, and
                what was on its left.
        """
        raise ParserSyntaxError(
            "Unexpected token %s in the middle of an expression (pos: %d)" % (
            self, context.current_pos))


class RightParen(Token):
    """A right parenthesis."""
    def __repr__(self):  # pragma: no cover
        return '<)>'


class LeftParen(Token):
    """A left parenthesis."""

    match = RightParen

    def nud(self, context):
        # Fetch the next expression
        expr = context.expression()
        # Eat the next token from the flow, and fail if it isn't a right
        # parenthesis.
        context.consume(expect_class=self.match)
        return expr

    def __repr__(self):  # pragma: no cover
        return '<(>'


class EndToken(Token):
    """Marks the end of the input."""
    lbp = 0

    def nud(self, context):
        raise ParserSyntaxError("Empty token flow.")

    def led(self, left, context):
        raise ParserSyntaxError("Unfinished token flow.")

    def __repr__(self):
        return '<End>'


class Parser(object):
    """Converts lexed tokens into their representation.

    Attributes:
        tokens (iterable of Token): the tokens.
        current_token (Token): the current token
    """

    def __init__(self, tokens):
        self.tokens = iter(tokens)
        self.current_pos = 0
        try:
            self.current_token = next(self.tokens)
        except StopIteration:
            raise ValueError("No tokens provided.")

    def _forward(self):
        try:
            self.current_token = next(self.tokens)
        except StopIteration:
            raise ParserSyntaxError("Unexpected end of token stream at %d." %
                self.current_pos)
        self.current_pos += 1

    def consume(self, expect_class=None):
        """Retrieve the current token, then advance the parser.

        If an expected class is provided, it will assert that the current token
        matches that class (is an instance).

        Note that when calling a token's nud() or led() functions, the "current"
        token is the token following the token whose method has been called.

        Returns:
            Token: the previous current token.
        """
        if expect_class and not isinstance(self.current_token, expect_class):
            raise ParserSyntaxError("Unexpected token at %d: got %r, expected %s" % (
                self.current_pos, self.current_token, expect_class.__name__))

        current_token = self.current_token
        self._forward()
        return current_token

    def expression(self, rbp=0):
        """Extract an expression from the flow of tokens.

        Args:
            rbp (int): the "right binding power" of the previous token.
                This represents the (right) precedence of the previous token,
                and will be compared to the (left) precedence of next tokens.

        Returns:
            Whatever the led/nud functions of tokens returned.
        """
        prev_token = self.consume()

        # Retrieve the value from the previous token situated at the
        # leftmost point in the expression
        left = prev_token.nud(context=self)

        while rbp < self.current_token.lbp:
            # Read incoming tokens with a higher 'left binding power'.
            # Those are tokens that prefer binding to the left of an expression
            # than to the right of an expression.
            prev_token = self.consume()
            left = prev_token.led(left, context=self)

        return left

    def parse(self):
        """Parse the flow of tokens, and return their evaluation."""
        return self.expression()


class Lexer(object):
    """The core lexer.

    From its list of tokens (provided through the TOKENS class attribute or
    overridden in the _tokens method), it will parse the given text, with the
    following rules:
    - For each (token, regexp) pair, try to match the regexp at the beginning
      of the text
    - If this matches, add token_class(match) to the list of tokens and continue
    - Otherwise, if the first character is either ' ' or '\t', skip it
    - Otherwise, raise a ValueError.

    Attributes:
        tokens (Token, re) list: The known tokens, as a (token class, regexp) list.
    """

    def __init__(self, default_tokens=True, blank_chars=(' ', '\t'), *args, **kwargs):
        self.tokens = []
        self.blank_chars = set(blank_chars)
        if default_tokens:
            self.register_token(LeftParen, re.compile(r'\('))
            self.register_token(RightParen, re.compile(r'\)'))

        super(Lexer, self).__init__(*args, **kwargs)

    def register_token(self, token_class, regexp):
        self.tokens.append((token_class, regexp))

    def _get_token(self, text):
        """Retrieve the next token from some text.

        Args:
            text (str): the text from which tokens should be extracted

        Returns:
            (token_kind, token_text): the token kind and its content.
        """
        for kind, regexp in self.tokens:
            match = regexp.match(text)
            if match:
                return kind, match
        return None, None

    def lex(self, text):
        """Split self.text into a list of tokens.

        Args:
            text (str): text to parse

        Yields:
            Token: the tokens generated from the given text.
        """
        while text:
            token_class, match = self._get_token(text)
            if token_class is not None:
                matched_text = text[match.start():match.end()]
                yield token_class(matched_text)
                text = text[match.end():]
            elif text[0] in self.blank_chars:
                text = text[1:]
            else:
                raise ValueError('Invalid character %s in %s' % (text[0], text))

        yield EndToken()

    def parse(self, text):
        """Parse self.text.

        Args:
            text (str): the text to lex

        Returns:
            object: a node representing the current rule.
        """
        tokens = self.lex(text)
        parser = Parser(tokens)
        return parser.parse()
