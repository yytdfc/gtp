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
    return " ".join([gtp_color(color), gtp_vertex(x, y)])


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


def format_success(message_id, response=None):
    if response is None:
        response = ""
    else:
        response = " {}".format(response)
    if message_id:
        return "={}{}\n\n".format(message_id, response)
    else:
        return "={}\n\n".format(response)


def format_error(message_id, response):
    if response is None:
        response = ""
    else:
        response = " {}".format(response)
    if message_id:
        return "?{}{}\n\n".format(message_id, response)
    else:
        return "?{}\n\n".format(response)


class Engine(object):

    def __init__(self):

        self.size = 19
        self.komi = 6.5
        # self.time_settings
        self.clear()

        self.disconnect = False

        self.known_commands = [
            field[4:] for field in dir(self) if field.startswith("cmd_")]

    def clear(self):
        self.board_configuration = [EMPTY] * (self.size * self.size)
        self.captured_B = 0
        self.captured_W = 0
        self.move_history = []

    def send(self, message):
        message_id, command, arguments = parse_message(message)
        if command in self.known_commands:
            try:
                return format_success(
                    message_id, getattr(self, "cmd_" + command)(arguments))
            except ValueError as exception:
                return format_error(message_id, exception.args[0])
        else:
            return format_error(message_id, "unknown command")

    def make_move(self, color, x, y):
        offset = self.size * (x - 1) + y - 1
        if self.board_configuration[offset] != EMPTY:
            return False
        # @@@ no other checks for now (e.g. suicide, ko)
        self.board_configuration[offset] = color
        self.move_history.append((color, x, y))
        return True

    # commands

    def cmd_protocol_version(self, arguments):
        return 2

    def cmd_name(self, arguments):
        return "gtp (python library)"

    def cmd_version(self, arguments):
        return "0.1"

    def cmd_known_command(self, arguments):
        return gtp_boolean(arguments in self.known_commands)

    def cmd_list_commands(self, arguments):
        return gtp_list(self.known_commands)

    def cmd_quit(self, arguments):
        self.disconnect = True

    def cmd_boardsize(self, arguments):
        if arguments.isdigit:
            size = int(arguments)
            if MIN_BOARD_SIZE <= size <= MAX_BOARD_SIZE:
                self.size = size
            else:
                raise ValueError("unacceptable size")

    def cmd_clear_board(self, arguments):
        self.clear()

    def cmd_komi(self, arguments):
        try:
            self.komi = float(arguments)
        except ValueError:
            raise ValueError("syntax error")

    def cmd_play(self, arguments):
        move = parse_move(arguments)
        if move:
            color, x, y = move
            if 1 <= x <= self.size and 1 <= y <= self.size:
                if self.make_move(color, x, y):
                    return
        raise ValueError("illegal move")

    def cmd_genmove(self, arguments):
        parse_color(arguments)
        # @@@ return a fixed vertex for now
        return gtp_vertex(16, 16)
