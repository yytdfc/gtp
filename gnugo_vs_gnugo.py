#!/usr/bin/env python

from subprocess import Popen, PIPE

from gtp import parse_vertex, gtp_move, gtp_color
from gtp import BLACK, WHITE, PASS, RESIGN


class GTPSubProcess(object):

    def __init__(self, label, args):
        self.label = label
        self.subprocess = Popen(args, stdin=PIPE, stdout=PIPE)
        print("{} subprocess created".format(label))

    def send(self, data):
        print("\33[0;31m{}\33[0;34m -> {}\33[0m".format(self.label, data.strip()))
        self.subprocess.stdin.write(data)
        result = ""
        while True:
            data = self.subprocess.stdout.readline()
            if not data.strip():
                break
            result += data
        if result.strip() != '=':
            print("{} \33[0;36m {}\33[0m".format(' '*len(self.label), result.strip()))
        return result

    def close(self):
        print("quitting {} subprocess".format(self.label))
        self.subprocess.communicate("quit\n")
    def set_label(self, label):
        self.label = label


class GTPFacade(object):

    def __init__(self, label, args):
        self.label = label
        # self.label = args[0]+'('+label+')'
        self.gtp_subprocess = GTPSubProcess(self.label, args)

    def name(self):
        self.label = self.gtp_subprocess.send("name\n")[1:].strip()
        self.gtp_subprocess.set_label(self.label)

    def version(self):
        self.gtp_subprocess.send("version\n")

    def boardsize(self, boardsize):
        self.gtp_subprocess.send("boardsize {}\n".format(boardsize))

    def komi(self, komi):
        self.gtp_subprocess.send("komi {}\n".format(komi))

    def clear_board(self):
        self.gtp_subprocess.send("clear_board\n")

    def genmove(self, color):
        message = self.gtp_subprocess.send(
            "genmove {}\n".format(gtp_color(color)))
        assert message[0] == "="
        return parse_vertex(message[1:].strip())

    def showboard(self):
        self.gtp_subprocess.send("showboard\n")

    def play(self, color, vertex):
        self.gtp_subprocess.send("play {}\n".format(gtp_move(color, vertex)))

    def final_score(self):
        return self.gtp_subprocess.send("final_score\n")[2]

    def close(self):
        self.gtp_subprocess.close()

    def time_settings(self, main_time, byo_time, byo_stones):
        self.gtp_subprocess.send("time_settings {} {} {}\n".format(main_time, byo_time, byo_stones))

    def get_label(self):
        return self.label


gnugo = ["gnugo", "--mode", "gtp"]
GNUGO_LEVEL_ONE = ["gnugo", "--mode", "gtp", "--level", "1"]
GNUGO_MONTE_CARLO = ["gnugo", "--mode", "gtp", "--monte-carlo"]
leela = ["leela_gtp", "-g", "--noponder"]
leelacl = ["leela_gtp_opencl", "-g", "--noponder"]
pachi = ["pachi", "-f/usr/games/book.dat", "-t1","threads=8,max_tree_size=8072,pondering=0"]


# black = GTPFacade("gnugo(black)", GNUGO)
engines_list = [leela, pachi]
scores={}
BOARDSIZE = 19
TIME = 5
for i in range(len(engines_list)):
    for j in range(len(engines_list)):
        if i==j:
            continue
        black = GTPFacade("", engines_list[i])
        white = GTPFacade("", engines_list[j])

        black.name()
        black.version()

        white.name()
        white.version()

        black.boardsize(BOARDSIZE)
        white.boardsize(BOARDSIZE)

        black.time_settings(0, TIME, 1)
        white.time_settings(0, TIME, 1)

        black.komi(6.5)
        white.komi(6.5)

        black.clear_board()
        white.clear_board()

        first_pass = False

        while True:
            vertex = black.genmove(BLACK)
            if vertex == RESIGN:
                break
            if vertex == PASS:
                if first_pass:
                    break
                else:
                    first_pass = True
            else:
                first_pass = False

            white.play(BLACK, vertex)

            vertex = white.genmove(WHITE)
            if vertex == RESIGN:
                break
            if vertex == PASS:
                if first_pass:
                    break
                else:
                    first_pass = True
            else:
                first_pass = False

            black.play(WHITE, vertex)

        if black.get_label() not in scores:
            scores[black.get_label()]=0
        if white.get_label() not in scores:
            scores[white.get_label()]=0
        if black.final_score()=='B':
            scores[black.get_label()]+=1
        else:
            scores[white.get_label()]+=1
        # white.final_score()

        black.close()
        white.close()
print(scores)
