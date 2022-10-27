import lzma

from math import nan
from statistics import mode
from typing_extensions import Self

_from_small_bytes = lambda x: int.from_bytes(x, "little")
_from_big_bytes = lambda x: int.from_bytes(x, "big")

def _get_data_point(data, length, conversionFn = lambda x: x):
    return [conversionFn(data[0:length]), data[length:]]

class BadReplayDataException(Exception):
    pass

class LifeGraph:
    __slots__ = ("data")

    def __init__(self, data):
        self.data = data

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, item):
        if self.data is None:
            return None
        if isinstance(item, slice | int):
            return self.data[item]
        elif isinstance(item, tuple):
            return tuple(self[point] for point in item)
        elif callable(item):
            return tuple(filter(item, self.data))
        raise TypeError("Indices must be slice, int, tuple[*(int | slice | function)], or a function that returns a boolean")

class Replay:
    MOUSE_LEFT = 1
    MOUSE_RIGHT = 2
    K1 = 4
    K2 = 8
    __slots__ = (
        "mode",
        "version",
        "beatmap_hash",
        "player_name",
        "replay_hash",
        "count_of_perfect",
        "count_of_good",
        "count_of_bad",
        "gekis",
        "katus",
        "misses",
        "score",
        "highest_combo",
        "is_perfect",
        "mods",
        "life_graph",
        "time_stamp_ns",
        "replay_data",
        "online_score_id",
        "additional_mod_information",
        "raw_input_data",
        "seed",
        "raw_data",
        "__total_x",
        "__total_y",
        "__mouse_left",
        "__mouse_right",
        "__k1",
        "__k2",
        "__mouse_left_frames",
        "__mouse_right_frames",
        "__k1_frames",
        "__k2_frames",
        "__map_len",
        "__map_len_including_intro"
    )
    def __init__(self):
        self.mode = None
        self.version  = None
        self.beatmap_hash = None
        self.player_name = None
        self.replay_hash = None
        self.count_of_perfect = None
        self.count_of_good = None
        self.count_of_bad = None
        self.gekis = None
        self.katus = None
        self.misses = None
        self.score = None
        self.highest_combo = None
        self.is_perfect = None
        self.mods = None
        self.life_graph: None | LifeGraph = None
        self.time_stamp_ns = None
        self.replay_data = None
        self.online_score_id = None
        self.additional_mod_information = None
        self.raw_input_data: tuple | None = None
        self.seed = None
        self.__total_x = None
        self.__total_y = None
        self.__mouse_left_frames = None
        self.__mouse_right_frames = None
        self.__k1_frames = None
        self.__k2_frames = None
        self.__mouse_left = None
        self.__mouse_right = None
        self.__k1 = None
        self.__k2 = None
        self.__map_len = None
        self.__map_len_including_intro = None
        self.raw_data = None

    def average_position(self) -> tuple[float, float]:
        """
        calculates the average position of the mouse
        """
        if self.raw_input_data is None:
            return (nan, nan)
        if self.__total_x is None:
            self.__total_x = sum(map(lambda x: x[1], self.raw_input_data))
        if self.__total_y is None:
            self.__total_y = sum(map(lambda x: x[2], self.raw_input_data))
        if self.raw_input_data is None:
            return (nan, nan)
        return self.__total_x / (len(self.raw_input_data)), self.__total_y / (len(self.raw_input_data) )

    def map_length(self):
        if self.__map_len is not None:
            return self.__map_len

        if self.life_graph is None:
            return -1

        start_after_intro = self.life_graph[0]
        end = self.life_graph[-1]
        if start_after_intro is None or end is None:
            return -1
        return end[0] - start_after_intro[0]

    def map_length_including_intro(self):
        if self.__map_len_including_intro is not None:
            return self.__map_len_including_intro

        if self.life_graph is None:
            return -1
        end = self.life_graph[-1]
        if end is None:
            return -1
        return end[0]


    @classmethod
    def from_file(cls, file):
        """
        Parse an osr file
        """
        with open(file, "rb") as f:
            data = f.read()

        replay_data = Replay()

        replay_data.raw_data = data

        [mode, data] = _get_data_point(data, 1, _from_big_bytes)

        replay_data.mode = mode

        if mode > 4:
            raise BadReplayDataException("Invalid osu replay file")

        [version, data] = _get_data_point(data, 4)

        replay_data.version = version

        #apparently if this is null the data is not there
        if(int(data[0]) ==0x0b):
            #offset because of \x0b
            data = data[1:]

            [hash_length, data] = _get_data_point(data, 1, _from_small_bytes)
            [beatmap_hash, data] = _get_data_point(data, hash_length, lambda x: x.decode("utf-8"))

            replay_data.beatmap_hash = beatmap_hash

        else: data = data[1:]

        if(int(data[0]) == 0x0b):
            #offset because of \x0b
            data = data[1:]
            [name_length, data] = _get_data_point(data, 1, _from_small_bytes)
            [name, data] = _get_data_point(data, name_length, lambda x: x.decode("utf-8"))
            replay_data.player_name = name

        else: data = data[1:]

        if(int(data[0]) == 0x0b):
            #offset because of \x0b
            data = data[1:]
            [hash_length, data] = _get_data_point(data, 1, _from_small_bytes)

            [replay_data.replay_hash, data] = _get_data_point(data, hash_length, lambda x: x.decode("utf-8"))
            
        else: data = data[1:]

        [threehundreds, data] = _get_data_point(data, 2, _from_small_bytes)
        replay_data.count_of_perfect = threehundreds

        [hundreds, data] = _get_data_point(data, 2, _from_small_bytes)
        replay_data.count_of_good = hundreds

        [fifties, data] = _get_data_point(data, 2, _from_small_bytes)
        replay_data.count_of_bad = fifties

        [gekis, data] = _get_data_point(data, 2, _from_small_bytes)
        replay_data.gekis = gekis

        [katus, data] = _get_data_point(data, 2, _from_small_bytes)
        replay_data.katus = katus

        [misses, data] = _get_data_point(data, 2, _from_small_bytes)
        replay_data.misses = misses

        [score, data] = _get_data_point(data, 4, _from_small_bytes)
        replay_data.score = score

        [biggest_combo, data] = _get_data_point(data, 2, _from_small_bytes)
        replay_data.highest_combo = biggest_combo

        [perfect, data] = _get_data_point(data, 1, lambda x: bool.from_bytes(x, "little"))
        replay_data.is_perfect = perfect

        [mods, data] = _get_data_point(data, 4, _from_small_bytes)

        replay_data.mods = mods

        #skipping \x0b
        if(int(data[0]) == 0x0b):
            data = data[1:]

            val = 0
            shift = 0
            i = 0
            while True:
                b = data[i]
                #idk what the heck this does it's horrifying
                #it's bit wise oring the result of the bitwise and of b and 127, then bitshifting it left
                val |= (b & 0x7f) << shift
                #doesn't this checks if b contains the highest bit in the binary number 128
                if (b & 0x80) == 0:
                    break
                #shift over by a bit for each bit that has been read?
                shift += 7
                i += 1
            data = data[i + 1:]

            chart = data[0:val]

            chart_data = chart.decode("utf-8").split(",")

            chart_data = (x for x in map(lambda x: x.split("|"), chart_data) if x[0])

            chart_data = tuple((int(t), float(l)) for t, l in chart_data)
            #
            data = data[val:]

            replay_data.life_graph = LifeGraph(chart_data)
                
        else: data = data[1:]

        [replay_data.time_stamp_ns, data] = _get_data_point(data, 8, _from_small_bytes)

        [replay_data_len, data] = _get_data_point(data, 4, _from_small_bytes)

        [replay_data.replay_data, data] = _get_data_point(data, replay_data_len, bytearray)

        [replay_data.online_score_id, data] = _get_data_point(data, 8, _from_small_bytes)
        with open("file.lzma", "wb") as f:
            f.write(replay_data.replay_data)

        player_inputs = lzma.open("file.lzma").read().decode("utf-8")

        groups = []
        for n in player_inputs.split(","):
            if not n: continue
            [ts, x, y, b] = n.split("|")
            ts = int(ts)
            x = float(x)
            y = float(y)
            b = int(b)
            groups.append((ts, x, y, b))

        if groups[-1][0] == -12345:
            replay_data.seed = groups[-1][3]
            groups = groups[:-1]

        replay_data.raw_input_data = tuple(groups)
        return replay_data

    def estimated_frame_rate(self) -> float:
        """
        calculates the frame rate based on the most common time between inputs
        assuming the player is holding down keys for more than 1 frame this should be somewhat accurate
        """
        if self.raw_input_data is None:
            return nan
        delays = map(lambda x: x[0], self.raw_input_data)
        mode_delay = mode(delays)
        return  1000 / 1 / mode_delay

    def click_count(self) -> tuple[int, int, int, int]:
        """
        Calculates the amount of frames left mouse, right mouse, k1, and k2 were held down

        Returns -1 if it can not be calculated
        """
        if self.__mouse_left_frames is not None \
                and self.__mouse_right_frames is not None \
                and self.__k1_frames is not None \
                and self.__k2_frames is not None:
            return (self.__mouse_right_frames, self.__mouse_right_frames, self.__k1_frames, self.__k2_frames)

        if self.raw_input_data is None:
            return (-1, -1, -1, -1)

        mouse_left = sum(map(lambda x: 1 if x[-1] & self.MOUSE_LEFT else 0, self.raw_input_data))
        mouse_right = sum(map(lambda x: 1 if x[-1] & self.MOUSE_RIGHT else 0, self.raw_input_data))
        k_1 = sum(map(lambda x: 1 if x[-1] & self.K1 else 0, self.raw_input_data))
        k_2 = sum(map(lambda x: 1 if x[-1] & self.K2 else 0, self.raw_input_data))

        self.__mouse_left_frames = mouse_left - k_1
        self.__mouse_right_frames = mouse_right - k_2
        self.__k1_frames = k_1
        self.__k2_frames = k_2
        return (mouse_left - k_1, mouse_right - k_2, k_1, k_2)

    def __true_count_of(self, key: int):
        if self.raw_input_data is None:
            return -1
        count = 0
        key_is_up = True
        for data_point in self.raw_input_data:
            if data_point[-1] & key and key_is_up is False:
                key_is_up = True
            elif not data_point[-1] & key and key_is_up:
                count += 1
                key_is_up = False
        return count

    def true_click_count(self) -> tuple[int, int, int, int]:
        """
        Gets the amount of times left, and right click were clicked
        and the amount of times k1, and k2 were pressed

        Returns -1 as the value if it can not be calculated
        """
        if self.__mouse_right is not None \
                and self.__mouse_left is not None \
                and self.__k1 is not None \
                and self.__k2 is not None:
            return (self.__mouse_left, self.__mouse_right, self.__k1, self.__k2)
        if self.raw_input_data is None:
            return (-1, -1, -1, -1)

        mouse_left = self.__true_count_of(self.MOUSE_LEFT)
        mouse_right = self.__true_count_of(self.MOUSE_RIGHT)
        k1 = self.__true_count_of(self.K1)
        k2 = self.__true_count_of(self.K2)

        self.__k1 = k1
        self.__k2 = k2
        self.__mouse_left = mouse_left - k1
        self.__mouse_right = mouse_right - k2
    
        return (mouse_left - k1, mouse_right - k2, k1, k2)

    @property
    def mouse_left(self) -> int:
        """
        Returns the amount of left clicks if calculated

        If not calculated, it will calculate the left click count
            This will also calculate the k1 key press count, as that is required
            to find the amount of left clicks

        Returns -1 if it can not be calculated
        """
        if self.__mouse_left is None:
            self.__k1 = self.__true_count_of(self.K1)
            self.__mouse_left = self.__true_count_of(self.MOUSE_LEFT) - self.__k1
            return self.__mouse_left

        return self.__mouse_left

    @property
    def mouse_right(self) -> int:
        """
        Returns the amount of right clicks if calculated

        If not calculated, it will calculate the right click count
            This will also calculate the k2 key press count, as that is required
            to find the amount of right clicks

        Returns -1 if it can not be calculated
        """

        if self.__mouse_right is None:
            self.__k2 = self.__true_count_of(self.K2)
            self.__mouse_right = self.__true_count_of(self.MOUSE_RIGHT) - self.__k2
            return self.__mouse_right

        return self.__mouse_right

    @property
    def k1(self) -> int:
        """
        Returns the amount of times k1 was pressed

        If not calculated, it will be calculated

        Returns -1 if it can not be calculated
        """

        if self.__k1 is None:
            self.__k1 = self.__true_count_of(self.K1)
            return self.__k1

        return self.__k1

    @property
    def k2(self) -> int:
        """
        Returns the amount of times k2 was pressed

        If not calculated, it will be calculated

        Returns -1 if it can not be calculated
        """

        if self.__k2 is None:
            self.__k2 = self.__true_count_of(self.K2)
            return self.__k2

        return self.__k2


    @property
    def k1_frames(self) -> int:
        """
        Returns the amount of frames k1 was held down

        If not calculated, it will be calculated

        Returns -1 if it can not be calculated
        """
        if self.raw_input_data is None:
            return -1

        if self.__k1_frames is None:
            return sum(map(lambda x: 1 if x[-1] & self.K1 else 0, self.raw_input_data))

        return self.__k1_frames

    @property
    def mouse_left_frames(self) -> int:
        """
        Returns the amount of frames mouse left was held down.

        If not calculated, it will be calculated, along with k1_frames, as it is required

        Returns -1 if it can not be calculated
        """
        if self.raw_input_data is None:
            return -1

        if self.__mouse_left_frames is None:
            if self.__k1_frames is None:
                self.__k1_frames = self.k1_frames
            self.__mouse_left_frames =  sum(map(lambda x: 1 if x[-1] & self.MOUSE_LEFT else 0, self.raw_input_data)) - self.__k1_frames

        return self.__mouse_left_frames

    @property
    def k2_frames(self) -> int:
        """
        Returns the amount of frames k2 was held down

        If not calculated, it will be calculated

        Returns -1 if it can not be calculated
        """

        if self.raw_input_data is None:
            return -1
        if self.__k1_frames is None:
            return sum(map(lambda x: 1 if x[-1] & self.K1 else 0, self.raw_input_data))

        return self.__k1_frames

    @property
    def mouse_right_frames(self) -> int:
        """
        Returns the amount of frames mouse right was held down.

        If not calculated, it will be calculated, along with k2_frames, as it is required

        Returns -1 if it can not be calculated
        """

        if self.raw_input_data is None:
            return -1

        if self.__mouse_right_frames is None:
            if self.__k2_frames is None:
                self.__k2_frames = self.k2_frames
            self.__mouse_right_frames =  sum(map(lambda x: 1 if x[-1] & self.MOUSE_RIGHT else 0, self.raw_input_data)) - self.__k2_frames

        return self.__mouse_right_frames

    @property
    def input_data(self):
        """
        synonymous with raw_input_data
        """
        return self.raw_input_data

    def __hash__(self):
        if not self.replay_hash:
            return -1
        return int(self.replay_hash, 16)

    def __iter__(self):
        if self.raw_input_data:
            return iter(self.raw_input_data)
        return tuple()

    def __getitem__(self, item):
        if self.raw_input_data is None:
            return None
        if isinstance(item, slice | int):
            return self.raw_input_data[item]
        elif isinstance(item, tuple):
            return tuple(self[point] for point in item)
        elif callable(item):
            return tuple(filter(item, self.raw_input_data))
        raise TypeError("Indices must be slice, int, tuple[*(int | slice | function)], or a function that returns a boolean")

    def __int__(self):
        if self.score is None:
            return -1
        return int(self.score)

    def __len__(self):
        return self.map_length()

    def __repr__(self):
        return repr(self.raw_input_data)

    def __str__(self):
        return str(self.raw_input_data)

    def __bytes__(self):
        if self.raw_data is None:
            return b''
        return self.raw_data

def main():
    import sys
    if len(sys.argv) < 2:
        print("\033[31mNo replay file given\033[0m")
        exit(1)

    replay = Replay.from_file(sys.argv[1])

    print(replay.player_name)

if __name__ == '__main__':
    main()
