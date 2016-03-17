#!/usr/bin/env python


import re


def pre_engine(s):
    s = re.sub("[^\t\n -~]", "", s)
    s = s.split("#")[0]
    s = s.replace("\t", " ")
    return s


def pre_controller(s):
    s = re.sub("[^\t\n -~]", "", s)
    s = s.replace("\t", " ")
    return s


def gtp_boolean(b):
    return "true" if b else "false"


def gtp_list(l):
    return "\n".join(l)


def gtp_color(color):
    # an arbitrary choice amongst a number of possibilities
    return {BLACK: "B", WHITE: "W"}[color]


def gtp_vertex(x, y):
    return "{}{}".format("ABCDEFGHJKLMNOPQRSTYVWYZ"[x - 1], y)


def gtp_move(color, x, y):
    return " ".join(gtp_color(color), gtp_vertex(x, y))


def parse_message(message):
    message = pre_engine(message).strip()
    first, rest = (message.split(" ", 1) + [None])[:2]
    if first.isdigit():
        message_id = int(first)
        if rest is not None:
            command, arguments = (rest.split(" ", 1) + [None])[:2]
        else:
            command, arguments = None, None
    else:
        message_id = None
        command, arguments = first, rest

    return message_id, command, arguments


WHITE = -1
BLACK = +1
EMPTY = 0


def parse_color(color):
    if color.lower() in ["b", "black"]:
        return BLACK
    elif color.lower() in ["w", "white"]:
        return WHITE
    else:
        return False


def parse_move(move):
    color, vertex = (move.split(" ") + [None])[:2]
    color = parse_color(color)
    if color is False:
        return False
    if vertex and len(vertex) > 1:
        x = "abcdefghjklmnopqrstuvwxyz".find(vertex[0].lower()) + 1
        if x == 0:
            return False
        if vertex[1:].isdigit():
            y = int(vertex[1:])
        else:
            return False
    else:
        return False

    return color, x, y


MIN_BOARD_SIZE = 7
MAX_BOARD_SIZE = 19


KNOWN_COMMANDS = [

    # 6.3.1 Administrative Commands
    "protocol_version", "name", "version",
    "known_command", "list_commands", "quit",

    # 6.3.2 Setup Commands
    "boardsize", "clear_board", "komi",
    # "fixed_handicap", "place_free_handicap", "set_free_handicap",

    # 6.3.3 Core Play Commands
    "play", "genmove",
    # "undo",

    # 6.3.4 Tournament Commands
    # "time_settings", "time_left", "final_score", "final_status_list",

    # 6.3.5 Regression Commands
    # "loadsgf", "reg_genmove",

    # 6.3.6 Debug Commands
    # "showboard",
]


class Engine(object):

    def __init__(self):

        self.size = 19
        self.komi = 6.5
        # self.time_settings
        self.clear()

        self.disconnect = False

    def clear(self):
        self.board_configuration = [EMPTY] * (self.size * self.size)
        self.captured_B = 0
        self.captured_W = 0
        self.move_history = []

    def send(self, message):
        message_id, command, arguments = parse_message(message)
        if command == "protocol_version":
            return self.success(message_id, self.protocol_version(arguments))
        elif command == "name":
            return self.success(message_id, self.name(arguments))
        elif command == "version":
            return self.success(message_id, self.version(arguments))
        elif command == "known_command":
            return self.success(message_id, self.known_command(arguments))
        elif command == "list_commands":
            return self.success(message_id, self.list_commands(arguments))
        elif command == "quit":
            return self.success(message_id, self.quit(arguments))
        elif command == "boardsize":
            if self.boardsize(arguments):
                return self.success(message_id)
            else:
                return self.error(message_id, "unacceptable size")
        elif command == "clear_board":
            return self.success(message_id, self.clear_board(arguments))
        elif command == "komi":
            if self.set_komi(arguments):
                return self.success(message_id)
            else:
                return self.error(message_id, "syntax error")
        elif command == "play":
            if self.play(arguments):
                return self.success(message_id)
            else:
                return self.error(message_id, "illegal move")
        elif command == "genmove":
            return self.success(message_id, self.genmove(arguments))
        else:
            return self.error(message_id, "unknown command")

    def success(self, message_id, response=""):
        if response:
            response = " {}".format(response)
        if message_id:
            return "={}{}\n\n".format(message_id, response)
        else:
            return "={}\n\n".format(response)

    def error(self, message_id, response):
        if response:
            response = " {}".format(response)
        if message_id:
            return "?{}{}\n\n".format(message_id, response)
        else:
            return "?{}\n\n".format(response)

    def protocol_version(self, arguments):
        return 2

    def name(self, arguments):
        return "gtp (python library)"

    def version(self, arguments):
        return "0.1"

    def known_command(self, arguments):
        return gtp_boolean(arguments in KNOWN_COMMANDS)

    def list_commands(self, arguments):
        return gtp_list(KNOWN_COMMANDS)

    def quit(self, arguments):
        self.disconnect = True
        return ""

    def boardsize(self, arguments):
        if arguments.isdigit:
            size = int(arguments)
            if MIN_BOARD_SIZE <= size <= MAX_BOARD_SIZE:
                self.size = size
                return True
            else:
                return False

    def clear_board(self, arguments):
        self.clear()
        return ""

    def set_komi(self, arguments):
        try:
            self.komi = float(arguments)
            return True
        except ValueError:
            return False

    def play(self, arguments):
        move = parse_move(arguments)
        if move:
            color, x, y = move
            if 1 <= x <= self.size and 1 <= y <= self.size:
                if self.make_move(color, x, y):
                    return True
        return False

    def genmove(self, arguments):
        parse_color(arguments)
        # @@@ return a fixed vertex for now
        return gtp_vertex(16, 16)

    def make_move(self, color, x, y):
        offset = self.size * (x - 1) + y - 1
        if self.board_configuration[offset] != EMPTY:
            return False
        # @@@ no other checks for now (e.g. suicide, ko)
        self.board_configuration[offset] == color
        self.move_history.append((color, x, y))
        return True


if __name__ == "__main__":
    assert pre_engine("foo\rbar") == "foobar"
    assert pre_engine("foo\nbar") == "foo\nbar"
    assert pre_engine("foo\tbar") == "foo bar"
    assert pre_engine("foo # bar") == "foo "

    assert pre_controller("foo\rbar") == "foobar"
    assert pre_controller("foo\nbar") == "foo\nbar"
    assert pre_controller("foo\tbar") == "foo bar"

    assert parse_message("foo") == (None, "foo", None)
    assert parse_message("foo bar") == (None, "foo", "bar")
    assert parse_message("1 foo") == (1, "foo", None)
    assert parse_message("1 foo bar") == (1, "foo", "bar")
    assert parse_message("1") == (1, None, None)
    assert parse_message("") == (None, "", None)
    assert parse_message(" ") == (None, "", None)

    assert parse_move("B D4") == (BLACK, 4, 4)
    assert parse_move("C X") is False
    assert parse_move("WHITE q16 XXX") == (WHITE, 16, 16)

    engine = Engine()

    response = engine.send("foo\n")
    assert response == "? unknown command\n\n"

    response = engine.send("protocol_version\n")
    assert response == "= 2\n\n"
    response = engine.send("1 protocol_version\n")
    assert response == "=1 2\n\n"

    response = engine.send("2 name\n")
    assert response == "=2 gtp (python library)\n\n"

    response = engine.send("3 version\n")
    assert response == "=3 0.1\n\n"

    response = engine.send("4 known_command name\n")
    assert response == "=4 true\n\n"
    response = engine.send("5 known_command foo\n")
    assert response == "=5 false\n\n"

    response = engine.send("6 list_commands\n")
    assert response == "=6 protocol_version\nname\nversion\nknown_command\n" \
        "list_commands\nquit\nboardsize\nclear_board\nkomi\nplay\ngenmove\n\n"

    response = engine.send("7 boardsize 100")
    assert response == "?7 unacceptable size\n\n"
    response = engine.send("8 boardsize 19")
    assert response == "=8\n\n"

    response = engine.send("9 clear_board")
    assert response == "=9\n\n"

    response = engine.send("10 komi 6.5")
    assert response == "=10\n\n"
    response = engine.send("11 komi foo")
    assert response == "?11 syntax error\n\n"

    response = engine.send("12 play black D4")
    assert response == "=12\n\n"

    response = engine.send("13 genmove white")
    assert response == "=13 Q16\n\n"  # test player will always return this

    response = engine.send("99 quit\n")
    assert response == "=99\n\n"
