# Copyright (c) 2016 Adrien Guinet <adrien@guinet.me>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from arybo.lib.mba_impl_petanque import MBAImpl
from arybo.lib.mba_impl_petanque import simplify as simplify_vec
from arybo.lib.mba_impl_petanque import expand_esf as expand_esf_vec
from arybo.lib.mba_impl_petanque import simplify_inplace as simplify_inplace_vec
from arybo.lib.mba_impl_petanque import expand_esf_inplace as expand_esf_inplace_vec
from pytanque import Vector, Expr

def expr_contains(e, o):
    ''' Returns true if o is in e '''
    if o == e:
        return True
    if e.has_args():
        for a in e.args():
            if expr_contains(a, o):
                return True
    return False

def __call_impl_func(f,e):
    if isinstance(e, MBAVariable):
        ret = e.mba.from_vec(f(e.vec))
        ret.always_expand_esf(e._expand_esf)
        ret.always_simplify(e._always_simplify)
        return ret
    return f(e)

def __call_impl_func_inplace(f,e):
    if isinstance(e, MBAVariable):
        f(e.vec)
    else:
        f(e)

def simplify(e):
    ''' Simplify the expression or variable e. '''
    return __call_impl_func(simplify_vec, e)
def expand_esf(e):
    ''' Expand ESF in the expression or variable e. '''
    return __call_impl_func(expand_esf_vec, e)
def simplify_inplace(e):
    ''' Simplify **inplace** the expression or variable e. returns e for conveniance. '''
    __call_impl_func_inplace(simplify_inplace_vec, e)
    return e
def expand_esf_inplace(e):
    ''' Expand ESF **inplace** in the expression or variable e. returns e for conveniance. '''
    __call_impl_func_inplace(expand_esf_inplace_vec, e)
    return e

class MBAVariable(object):
    ''' Represents a symbolic variable in a given :class:`MBA` space.

    This object is the main object to use when computing expressions with arybo.
    It supports both the arithmetic and boolean logic, allowing the computation
    of expressions that use both arithmetics. The corresponding Python
    operators are overloaded, allowing to directly write expressions like this:

    >>> x = mba.var('x')
    >>> e = ((x+7)|10)//9

    It internally holds a :class:`pytanque.Vector` object that represents the
    n-bit expressions associated with this symbolic variable.
    '''

    def __init__(self, mba, arg):
        self.mba = mba
        self.arg = arg
        self._always_simplify = False
        self._expand_esf = False

    def __hash__(self):
        return id(self)

    def __gen_v(self, v):
        v = MBAVariable(self.mba, v)
        v.always_expand_esf(self._expand_esf)
        v.always_simplify(self._always_simplify)
        return v

    def __ret(self, v):
        if self._expand_esf:
            expand_esf_inplace(v)
        if self._always_simplify:
            simplify_inplace(v)
        return self.__gen_v(v)

    @classmethod
    def from_vec(cls, mba, data):
        return cls(mba, data)
    from_vector = from_vec

    @property
    def vec(self):
        ''' Returns the underlying vector object '''
        return self.arg
    vector = vec

    def at(self, idx):
        ''' Returns the boolean expression of the idx-th bit '''
        return self.arg[idx]

    def __call_op(self, name, o):
        if isinstance(o, int):
            fname = '%s_n' % name
        elif isinstance(o, Expr):
            fname = "%s_exp" % name
        else:
            fname = '%s_Y' % name
            o = o.vec
        ret = getattr(self.mba, fname)(self.vec, o)
        return self.__ret(ret)

    def __add__(self, o):
        return self.__call_op('add', o)

    def __iadd__(self, o):
        return self.__call_op('iadd', o)

    def __radd__(self, o):
        return self.__add__(o)

    def __sub__(self, o):
        return self.__call_op('sub', o)

    def __rsub__(self, o):
        if (isinstance(o, int)):
            return self.mba.from_cst(o)-self
        else:
            return o-self

    def __mul__(self, o):
        return self.__call_op('mul', o)

    def __rmul__(self, o):
        return self.__mul__(o)

    def __truediv__(self, o):
        return self.__call_op('div', o)

    def __xor__(self, o):
        return self.__call_op('xor', o)

    def __rxor__(self, o):
        return self.__xor__(o)

    def __and__(self, o):
        return self.__call_op('and', o)

    def __rand__(self, o):
        return self.__and__(o)

    def __or__(self, o):
        return self.__call_op('or', o)

    def __ror__(self, o):
        return self.__or__(o)

    def __lshift__(self, o):
        return self.__call_op('lshift', o)

    def __rshift__(self, o):
        return self.__call_op('rshift', o)

    def __invert__(self):
        return self.__ret(self.mba.not_X(self.vec))

    def __neg__(self):
        return self.__ret(self.mba.oppose_X(self.vec))

    def __repr__(self):
        return repr(self.arg)

    def __eq__(self, o):
        if isinstance(o, MBAVariable):
            o = o.vec
        return self.vec == o

    def __getitem__(self, idx):
        return self.at(idx)

    def evaluate(self, values):
        ''' Evaluates the expression to an integer

        values is a dictionnary that associates n-bit variables to integer
        values. Every symbolic variables used in the expression must be
        represented. 

        For instance, let x and y 4-bit variables, and e = x+y:

        >>> mba = MBA(4)
        >>> x = mba.var('x')
        >>> y = mba.var('y')
        >>> e = x+y

        To evaluate e with x=4 and y=5, we can do:

        >>> e.eval({x: 4, y: 5})
        9

        If a variable is missing from values, an exception will occur. (x
        or y in the example above)
        '''
        return self.mba.evaluate(self.vec, values)
    eval = evaluate

    def expand_esf(self):
        ''' Expand ESF in the expression '''
        return expand_esf(self)

    def simplify(self):
        ''' Simplify the expression '''
        return simplify(self)

    def expand_esf_and_simplify(self):
        ''' Expand and simplify the expression '''
        return self.expand_esf().simplify()

    def always_simplify(self, v=True):
        ''' If v is true, force a call to simplify each time an operation is done '''
        self._always_simplify = v

    def always_expand_esf(self, v=True):
        ''' Specify whether ESF should always be expanded '''
        self._expand_esf = v 

    def vectorial_decomp(self, symbols):
        ''' Compute the vectorial decomposition of the expression according to the given symbols.

        symbols is a list that represents the input of the resulting
        application. They are considerated as a flatten vector of bits.

        Args:
            symbols: TODO

        Returns:
            An :class:`pytanque.App` object

        Example:
            >>> mba = MBA(4)
            >>> x = mba.var('x')
            >>> y = mba.var('y')
            >>> e = x^y^6
            >>> e.vectorial_decomp([x,y])
            App NL = Vec([
            0,
            0,
            0,
            0
            ])
            AffApp matrix = Mat([
                [1, 0, 0, 0, 1, 0, 0, 0]
                [0, 1, 0, 0, 0, 1, 0, 0]
                [0, 0, 1, 0, 0, 0, 1, 0]
                [0, 0, 0, 1, 0, 0, 0, 1]
                ])
            AffApp cst = Vec([
                0,
                1,
                1,
                0
                ])
        '''
        try:
            symbols = [s.vec for s in symbols]
            N = sum(map(lambda s: len(s), symbols))
            symbols_ = Vector(N)
            i = 0
            for v in symbols:
                for s in v:
                    symbols_[i] = s
                    i += 1
            symbols = symbols_
        except TypeError: pass
        return self.mba.vectorial_decomp(symbols, self.vec)

    def to_cst(self):
        ''' Convert the expression to a constant if possible (that is only immediates are present) '''
        return self.mba.get_int(self.vec)

    def to_bytes(self):
        ''' Convert the expression to bytes if possible (that is only immediates are present).

        A current limitation is that the number of bits must be a multiple of 8.
        '''
        return self.mba.to_bytes(self.vec)


class MBA(MBAImpl):
    ''' Represents an MBA (Miwed Boolean Arithmetic) space of a fixed number of bits. '''
    def var(self, name):
        ''' Get an n-bit named symbolic variable

        Returns:
            An :class:`MBAVariable` object representing a symbolic variable

        Example:
            >>> mba.var('x')
            Vec([
            x0,
            x1,
            x2,
            x3
            ])
        '''

        return self.from_vec(self.var_symbols(name))

    def from_vec(self, v):
        ''' Get an :class:`MBAVariable` object with the vector's values.

        Args:
            v: a pytanque vector holding boolean expressions

        Returns:
            An :class:`MBAVariable` object with the vector's values
        '''
        return MBAVariable.from_vec(self, v)

    def evaluate(self, E, values):
        if isinstance(E, MBAVariable):
            E = E.vec
        return super(MBA, self).evaluate(E, values)

    def permut2expr(self, P):
        ''' Convert a substitution table into an arybo application

        Args:
            P: list of integers. The list must not contain more than 2**nbits elements.

        Returns:
            A tuple containing an :class:`MBAVariable` object with the result
            and the symbolic input variable used in this object. A typical use
            case is to feed these into vectorial_decomp.

        Example:
            >>> mba = MBA(4)
            >>> P = [i^7 for i in range(16)]
            >>> E,X = mba.permut2expr(P)
            >>> E.vectorial_decomp([X])
            App NL = Vec([
            0,
            0,
            0,
            0
            ])
            AffApp matrix = Mat([
            [1, 0, 0, 0]
            [0, 1, 0, 0]
            [0, 0, 1, 0]
            [0, 0, 0, 1]
            ])
            AffApp cst = Vec([
            1,
            1,
            1,
            0
            ])
        '''
        if len(P) > (1<<self.nbits):
            raise ValueError("P must not contain more than %d elements" % (1<<self.nbits))
        X = self.var('X')
        ret = super(MBA, self).permut2expr(P, X.vec)
        return self.from_vec(ret), X

    def symbpermut2expr(self, P):
        X = self.var('X')
        ret = super(MBA, self).symbpermut2expr(P, X.vec)
        return self.from_vec(ret), X

    def from_cst(self, C):
        return self.from_vec(self.get_vector_from_cst(C))

    def from_bytes(self, s):
        if not isinstance(s, bytes):
            raise ValueError("s must be an instance of bytes!")
        # TODO: fix this...
        if self.nbits % 8 != 0:
            raise ValueError("self.nbits must be a multiple of 8")
        nbytes = self.nbits//8
        if len(s) > nbytes:
            s = s[:nbytes]
        elif len(s) < nbytes:
            s = s + 'b\x00'*(nbytes-len(s))
        return self.from_vec(super(MBA, self).from_bytes(s))
