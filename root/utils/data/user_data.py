import pandas as pd


file = [pd.DataFrame(dtype=object)]
users = file[0]


class GetUsers:
    def __init__(self, user):
        self.__user = user

    async def __aenter__(self):
        self.__temp = self.__user[:]
        return self.__temp

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            self.__user[:] = self.__temp
        return False
