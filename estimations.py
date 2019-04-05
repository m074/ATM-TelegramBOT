import sqlite3
import datetime
import dateutil.parser


EMPTY_PROBABILITY_THRESHOLD = 0.5
MAX_EXTRACTION = 1000


class PersistentEstimator:
    def __init__(self, db_filename):
        self.__filename = db_filename
        self.__dict = dict()

        connection = sqlite3.connect(db_filename)
        cursor = connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS estimations
                 (id INT PRIMARY KEY, probability REAL, requests INT, date TEXT)''')
        connection.commit()

        for row in cursor.execute("SELECT id,probability,requests,date FROM estimations"):
            print(row)
            self.__dict[row[0]] = Estimation(row[1], row[2], dateutil.parser.parse(row[3]).date())
        connection.close()

    def is_probably_empty(self, bank):
        if bank.id not in self.__dict:
            return False
        return self.__dict[bank.id].is_probably_empty()

    def add(self, bank, probability):
        if bank.id not in self.__dict:
            self.__dict[bank.id] = Estimation(0)
        self.__dict[bank.id].add(probability)
        self.__update_db(bank)

    def __update_db(self, bank):
        connection = sqlite3.connect(self.__filename)
        cursor = connection.cursor()
        estimate = self.__dict[bank.id]
        tuple = cursor.execute("SELECT id FROM estimations WHERE id=?", [bank.id]).fetchone()
        if tuple is None:
            cursor.execute("INSERT INTO estimations VALUES (?,?,?,?)",
                           [bank.id,
                            estimate.probability,
                            estimate.request_quantity,
                            estimate.expiration_date.isoformat()])
        else:
            cursor.execute("UPDATE estimations SET probability = ?, requests = ?, date=?  WHERE id = ?",
                           [estimate.probability,
                            estimate.request_quantity,
                            estimate.expiration_date.isoformat(),
                            bank.id])
        connection.commit()
        connection.close()
        pass


class Estimation:
    def __init__(self, probability, request_quantity=0, expiration_date=None):
        self.probability = probability
        self.expiration_date = expiration_date
        self.request_quantity = request_quantity
        if expiration_date is None:
            self.expiration_date = self.__get_expiration_date(self.__today())

    @staticmethod
    def __get_expiration_date(dat):
        if dat.isoweekday() in [6, 7]:
            dat += datetime.timedelta(days=dat.isoweekday() % 5)
        dat += datetime.timedelta(days=1)
        return dat

    @staticmethod
    def __today():
        today = datetime.date.today()
        if datetime.datetime.now().hour < 8:
            today -= datetime.timedelta(days=1)
        return today

    def __probablity(self):
        if self.__today() >= self.expiration_date:
            self.probability = 0
            self.request_quantity = 0
            self.expiration_date = self.__get_expiration_date(self.__today())
        if self.request_quantity <= MAX_EXTRACTION:
            return 0
        return self.probability / MAX_EXTRACTION

    def is_probably_empty(self):
        return self.__probablity() > EMPTY_PROBABILITY_THRESHOLD

    def add(self, prob):
        if self.__today() >= self.expiration_date:
            self.probability = 0
            self.request_quantity = 0
            self.expiration_date = self.__get_expiration_date(self.__today())
        self.probability += prob
        self.request_quantity += 1
