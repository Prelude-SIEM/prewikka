# Copyright (C) 2018-2020 CS GROUP - France. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
#
# The following code is derived from Django CSRF middleware.
#
# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of Django nor the names of its contributors may be used
#        to endorse or promote products derived from this software without
#        specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import operator
import string

from prewikka import hookmanager
from prewikka.utils import crypto


CSRF_SECRET_LENGTH = 32
CSRF_TOKEN_LENGTH = 2 * CSRF_SECRET_LENGTH
CSRF_ALLOWED_CHARS = string.ascii_letters + string.digits
CSRF_POST_KEY = "_csrftoken"


def _hash_token(token, salt, op):
    chars = CSRF_ALLOWED_CHARS
    pairs = zip((chars.index(x) for x in token), (chars.index(x) for x in salt))
    cipher = ''.join(chars[op(x, y) % len(chars)] for x, y in pairs)
    return cipher


def _salt_cipher_secret(secret):
    """
    Given a secret (assumed to be a string of CSRF_ALLOWED_CHARS), generate a
    token by adding a salt and using it to encrypt the secret.
    """
    salt = _get_new_csrf_string()
    return salt + _hash_token(secret, salt, operator.add)


def _unsalt_cipher_token(token):
    """
    Given a token (assumed to be a string of CSRF_ALLOWED_CHARS, of length
    CSRF_TOKEN_LENGTH, and that its first half is a salt), use it to decrypt
    the second half to produce the original secret.
    """
    salt, token = token[:CSRF_SECRET_LENGTH], token[CSRF_SECRET_LENGTH:]
    return _hash_token(token, salt, operator.sub)


def _get_new_csrf_string():
    return crypto.get_random_string(CSRF_SECRET_LENGTH, allowed_chars=CSRF_ALLOWED_CHARS)


def _get_new_csrf_token():
    return _salt_cipher_secret(_get_new_csrf_string())


def get_token(request):
    """
    Return the CSRF token required for a POST form. The token is an
    alphanumeric value. A new token is created if one is not already set.
    """
    csrf_cookie = request.input_cookie.get('CSRF_COOKIE')
    if csrf_cookie:
        request._csrf_cookie = csrf_cookie.value
        csrf_secret = _unsalt_cipher_token(request._csrf_cookie)
    else:
        request._csrf_cookie = None
        csrf_secret = _get_new_csrf_string()

    return _salt_cipher_secret(csrf_secret)


def _compare_salted_tokens(request_csrf_token, csrf_token):
    return crypto.constant_time_compare(_unsalt_cipher_token(request_csrf_token), _unsalt_cipher_token(csrf_token))


def process(request):
    # Update the cookie token on each request, previous token issued with the same
    # CSRF string will still match.
    request.add_cookie("CSRF_COOKIE", get_token(request))

    if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
        return

    if request.get_origin() != request.get_target_origin():
        raise Exception("Origin check failed")

    if request._csrf_cookie is None:
        raise Exception("CSRF cookie not set")

    # Check non-cookie token for match.
    request_csrf_token = request.arguments.get(CSRF_POST_KEY)
    if not request_csrf_token:
        # Fall back to X-CSRFToken, to make things easier for AJAX,
        # and possible for PUT/DELETE.
        request_csrf_token = request.headers.get("x-csrftoken", '')
        if not request_csrf_token:
            raise Exception("CSRF token has not been provided")

    if not _compare_salted_tokens(request_csrf_token, request._csrf_cookie):
        raise Exception("CSRF token is invalid")


def _rotate_token(user):
    env.request.web.add_cookie("CSRF_COOKIE", _get_new_csrf_token())


hookmanager.register("HOOK_SESSION_CREATE", _rotate_token)
