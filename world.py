from enum import Enum

class Disease(Enum):
    BLUE = 0
    BLACK = 1
    RED = 2
    YELLOW = 3

class City(Enum):
    SAN_FRANCISCO = 0
    CHICAGO = 1
    MONTREAL = 2
    NEW_YORK = 3
    WASHINGTON = 4
    ATLANTA = 5
    MADRID = 6
    LONDON = 7
    PARIS = 8
    ESSEN = 9
    MILAN = 10
    ST_PETERSBURG = 11
    ALGIERS = 12
    ISTANBUL = 13
    MOSCOW = 14
    CAIRO = 15
    BAGHDAD = 16
    TEHRAN = 17
    DELHI = 18
    KARACHI = 19
    RIYADH = 20
    MUMBAI = 21
    CHENNAI = 22
    KOLKATA = 23
    BEIJING = 24
    SEOUL = 25
    TOKYO = 26
    SHANGHAI = 27
    HONG_KONG = 28
    TAIPEI = 29
    OSAKA = 30
    BANGKOK = 31
    HO_CHI_MINH_CITY = 32
    MANILA = 33
    JAKARTA = 34
    SYDNEY = 35
    KHARTOUM = 36
    JOHANNESBURG = 37
    KINSHASA = 38
    LAGOS = 39
    SAO_PAULO = 40
    BUENOS_AIRES = 41
    SANTIAGO = 42
    LIMA = 43
    BOGOTA = 44
    MEXICO_CITY = 45
    LOS_ANGELES = 46
    MIAMI = 47

color_map = [0]*12 + [1]*12 + [2]*12 + [3]*12