# coding: utf-8
from __future__ import print_function
import re
import sys
from ctypes import (
    util, CDLL, create_string_buffer, create_unicode_buffer, byref,
    c_byte, c_ubyte,
    c_short, c_ushort,
    c_int, c_uint,
    c_long, c_ulong,
    c_longlong, c_ulonglong,
    c_size_t,
    c_float, c_double, c_longdouble,
    c_char_p, c_wchar_p, c_void_p)

if sys.version_info < (3, 0):
    range = xrange
else:
    unicode = str

LIBC = CDLL(util.find_library('sscanf.dll'))

C_SCANF_TYPES = {
    'i'   : c_int,
    'hhi' : c_byte,
    'hi'  : c_short,
    'li'  : c_long,
    'lli' : c_longlong,
    'ji'  : c_longlong,
    'zi'  : c_size_t,
    'ti'  : c_longlong,

    'd'   : c_int,
    'hhd' : c_byte,
    'hd'  : c_short,
    'ld'  : c_long,
    'lld' : c_longlong,
    'jd'  : c_longlong,
    'zd'  : c_size_t,
    'td'  : c_longlong,

    'u'   : c_uint,
    'hhu' : c_ubyte,
    'hu'  : c_ushort,
    'lu'  : c_ulong,
    'llu' : c_ulonglong,
    'ju'  : c_ulonglong,
    'zu'  : c_size_t,
    'tu'  : c_longlong,

    'o'   : c_uint,
    'hho' : c_ubyte,
    'ho'  : c_ushort,
    'lo'  : c_ulong,
    'llo' : c_ulonglong,
    'jo'  : c_ulonglong,
    'zo'  : c_size_t,
    'to'  : c_longlong,

    'x'   : c_uint,
    'hhx' : c_ubyte,
    'hx'  : c_ushort,
    'lx'  : c_ulong,
    'llx' : c_ulonglong,
    'jx'  : c_ulonglong,
    'zx'  : c_size_t,
    'tx'  : c_longlong,

    'f'   : c_float,
    'lf'  : c_double,
    'Lf'  : c_longdouble,
    'e'   : c_float,
    'le'  : c_double,
    'Le'  : c_longdouble,
    'g'   : c_float,
    'lg'  : c_double,
    'Lg'  : c_longdouble,
    'a'   : c_float,
    'la'  : c_double,
    'La'  : c_longdouble,

    'c'   : lambda l: lambda : create_string_buffer(l),  # c_char_p,
    'lc'  : lambda l: lambda : create_unicode_buffer(l),  # c_wchar_p,
    's'   : lambda l: lambda : create_string_buffer(l),  # c_char_p,
    'ls'  : lambda l: lambda : create_unicode_buffer(l),  # c_wchar_p,
    
    ']'   : lambda l: lambda : create_string_buffer(l),  # c_char_p,
    #'l[]' : c_wchar_p, handled in _get_c_object

    'p'   : c_void_p,

    'n'   : c_int,
    'hhn' : c_byte,
    'hn'  : c_short,
    'ln'  : c_long,
    'lln' : c_longlong,
    'jn'  : c_longlong,
    'zn'  : c_size_t,
    'tn'  : c_longlong,
}

SPECIFIER = re.compile('%([^ \t\n\r\f\v%%*]+)')


class IllegalSpecifier(Exception): pass


def _get_c_object(part, length):
    ctor = None

    # search most appropriate type constructor
    for pos in range(len(part)):
        try:
            ctor = C_SCANF_TYPES[part[-(pos+1):]]
        except KeyError:
            break
    if not ctor:
        raise IllegalSpecifier('cannot handle specifier "%%%s"' % part)

    # special handling of string types
    if part[-1:] in ('c', 's', ']'):
        # create unicode type for l[]
        if part[-1:] == ']' and part.find('l[') != -1:
            ctor = lambda l: lambda : create_unicode_buffer(l)
        # string buffers with length of input string
        ctor = ctor(length)
    return ctor()

def sscanf(fmt, s):
    """
    clib sscanf for Python.
    For unicode strings use the l-versions of the string specifiers
    (%ls instead of %s).

    Returns a list with filled specifiers in order.
    """
    length = len(s)
    args = [_get_c_object(part, length) for part in SPECIFIER.findall(fmt)]
    sscanf_func = LIBC.sscanf
    buffer_ctor = create_string_buffer
    if isinstance(s, unicode):
        sscanf_func = LIBC.swscanf
        buffer_ctor = create_unicode_buffer
    filled = sscanf_func(buffer_ctor(s), buffer_ctor(fmt), *map(byref, args))
    return [args[i].value for i in range(filled)]


if __name__ == '__main__':
    print(sscanf('%s %s %%%% %s', 'abc defg %% bbb'))
    print(sscanf(u'%ls %ls %%%% %s', u'abc defg %% bbb'))

    print(sscanf(u'%ls', u'äüöß'))

    print(sscanf('%5c %s - %d %f %x', 'ttttt abc - 123 -123.12345e-12 1b'))
    print(sscanf(u'%5lc %ls - %d %f %x', u'ttttt abc - 123 -123.12345e-12 1b'))

    print(sscanf('%*5c%s', 'tttttabc'))
    print(sscanf(u'%*5lc%s', u'tttttabc'))

    print(sscanf(u'%3l[ä]%*l[ä] %d', u'ääääääääääää 1'))
