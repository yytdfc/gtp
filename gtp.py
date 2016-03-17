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
