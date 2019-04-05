import math
import itertools

RADIO = 0.5  # in kms


class Bank:
    def __init__(self, id, network, name, address, position):
        self.id = id
        self.position = position
        self.network = network
        self.name = name
        self.address = address


class BanksGrid:
    def __init__(self, bank_list):
        # la idea es generar una matriz en un rectangulo (segun Mercanter) donde contengan todos los bancos
        # la matriz dividira en rectangulos de 500 x 500 metros como minimo
        self.__min_lat = min(map(lambda x: x.position[0], bank_list))
        self.__min_lng = min(map(lambda x: x.position[1], bank_list))

        self.__max_lat = max(map(lambda x: x.position[0], bank_list))
        self.__max_lng = max(map(lambda x: x.position[1], bank_list))

        self.__dist_lat = self.__calculate_distance((self.__min_lat, self.__max_lng), (self.__max_lat, self.__max_lng))
        extrme_lat = max(abs(self.__max_lat), abs(self.__min_lat))
        self.__dist_lng = self.__calculate_distance((extrme_lat, self.__min_lng),
                                                    (extrme_lat, self.__max_lng))

        self.__diff_lat = abs(self.__max_lat - self.__min_lat)
        self.__diff_lng = abs(self.__max_lng - self.__min_lng)

        self.__x_frames, self.__y_frames = math.floor(self.__dist_lat // RADIO), math.floor(self.__dist_lng // RADIO)

        self.__grid_by_network = dict()

        for bank in bank_list:
            if bank.network not in self.__grid_by_network:
                self.__grid_by_network[bank.network] = [[list() for j in range(self.__y_frames + 1)]
                                                        for i in range(self.__x_frames + 1)]
            inx_lat, inx_lng = self.__matrix_index(bank.position)
            self.__grid_by_network[bank.network][inx_lat][inx_lng].append(bank)

    @staticmethod
    def __calculate_distance(origin, destination):
        lat1, lng1 = origin
        lat2, lng2 = destination
        radius = 6371  # km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lng2 - lng1)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) \
            * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = radius * c

        return distance

    def __matrix_index(self, position):
        x = math.floor((position[0] - self.__min_lat) / (self.__diff_lat / self.__x_frames))
        y = math.floor((position[1] - self.__min_lng) / (self.__diff_lng / self.__y_frames))
        return x, y

    def nearest_banks(self, position, network, estimator):
        x, y = self.__matrix_index(position)
        nearest_bank_list = []
        for i, j in itertools.product([-1, 0, 1], repeat=2):

            try:
                if x + i < 0 or y + j < 0:
                    raise IndexError
                for bank in self.__grid_by_network[network][x + i][y + j]:
                    if estimator.is_probably_empty(bank):
                        continue
                    distance = self.__calculate_distance(position, bank.position)
                    if distance <= RADIO:
                        nearest_bank_list.append([distance, bank])
            except IndexError:
                pass

        nearest_bank_list = sorted(nearest_bank_list, key=lambda x: x[0])[:3]
        extraction_probability = [0.7, 0.2, 0.1]
        for index, (distance, bank) in enumerate(nearest_bank_list):
            estimator.add(bank, extraction_probability[index])
        return nearest_bank_list
