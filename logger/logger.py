from tinydb import TinyDB
from datetime import datetime


class Logger:

    @staticmethod
    def log_move(operation: str, data: dict):
        db = TinyDB('db.json')

        log = {
            'operation': operation,
            'date': datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        }

        log.update(data)
        db.insert(log)