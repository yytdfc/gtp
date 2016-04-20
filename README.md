# gtp

[![Build Status](https://travis-ci.org/jtauber/gtp.svg)](https://travis-ci.org/jtauber/gtp)
[![Coverage Status](https://coveralls.io/repos/jtauber/gtp/badge.svg?branch=master&service=github)](https://coveralls.io/github/jtauber/gtp?branch=master)

Python implementation of Go Text Protocol that can interface with arbitrary player and state implementations, provided that they conform to the following interface

## State interface

`clear()` : clear the board, scores, and history

`make_move(color, vertex)` : play a move. `color` is `-1` for white, `+1` for black. `vertex` is a tuple of 1-indexed `(x,y)` coordinates. This function should return `True` on success and `False` on any error

`set_size(n)` : set the size of the board to `n x n`. The protocol does not specify what happens to existing stones or history.

`set_komi(k)` : set komi value to `k`

## Player interface

`get_move(state, c)` : choose a move for color `c` given the state object. Returns a tuple `(x,y)`, where `(0,0)` indicates a PASS
