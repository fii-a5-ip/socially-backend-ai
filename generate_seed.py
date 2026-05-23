import random
import os

loc_tags = {
    10: [147, 75, 85, 163],
    11: [171, 85, 27, 193],
    12: [159, 156, 145, 164],
    13: [46, 61, 85, 101],
    14: [184, 183, 95, 118],
    15: [210, 13, 118],
    16: [194, 192, 64, 118],
    17: [24, 25, 163, 156],
    18: [37, 156, 159],
    19: [159, 156, 145, 164],
    20: [62, 61, 46, 85],
    21: [216, 217, 175, 95],
    22: [175, 167, 95, 77],
    23: [171, 85, 27, 134],
    24: [195, 192, 98, 156],
    25: [62, 61, 46, 101]
}

loc_names = {
    10: 'Viper Club', 11: 'Time Out', 12: 'Zona de Agrement Ciric', 13: 'Cafeneaua Acaju',
    14: 'Palas Mall', 15: 'Teatrul National', 16: 'Sala Polivalenta', 17: 'Tiki Village',
    18: 'Gradina Botanica', 19: 'Parcul Copou', 20: 'Jassyro', 21: 'Cuib', 22: 'Mamma Mia',
    23: 'Legend Pub', 24: 'Stadionul Emil Alexandrescu', 25: 'Tucano Coffee'
}

event_tags = {
    10: [61, 46, 85], 11: [61, 35, 46], 12: [78, 61, 95], 13: [146, 61, 46], 14: [33, 61, 103],
    15: [178, 175, 95], 16: [121, 182, 175, 95], 17: [216, 217, 95], 18: [41, 95], 19: [120, 175, 95],
    20: [167, 94, 95], 21: [44, 64, 93], 22: [198, 93, 95], 23: [175, 95, 179], 24: [140, 95],
    25: [134, 65, 144], 26: [173, 171, 103], 27: [76, 27, 64], 28: [134, 144, 65], 29: [123, 144, 163],
    30: [163, 75, 148], 31: [24, 83, 163, 75], 32: [60, 163, 85], 33: [163, 147, 75], 34: [187, 75, 163],
    35: [210, 13], 36: [14, 90, 13], 37: [88, 13], 38: [143, 13], 39: [210, 13], 40: [234, 227, 156],
    41: [166, 156, 188], 42: [164, 159, 156], 43: [37, 88, 145], 44: [35, 156, 159], 45: [183, 184],
    46: [57, 118], 47: [90, 13], 48: [103, 64], 49: [233, 125, 13], 50: [98, 195, 192], 51: [22, 194, 192],
    52: [138, 64, 192], 53: [192, 156], 54: [135, 171, 192]
}

sql = []
sql.append('SET FOREIGN_KEY_CHECKS = 0;')
sql.append('DELETE FROM user_filters;')
sql.append('DELETE FROM location_filters;')
sql.append('DELETE FROM event_filters;')
sql.append('SET FOREIGN_KEY_CHECKS = 1;')
sql.append('')

sql.append('-- LOCATIONS UPDATES (Addresses)')
for lid, name in loc_names.items():
    escaped = name.replace("'", "''")
    sql.append(f"UPDATE locations SET country = 'Romania', state_county = 'Iasi', city = 'Iasi', street = 'Strada {escaped}', formatted_address = '{escaped}, Iasi, Romania' WHERE id = {lid};")
sql.append('')

sql.append('-- LOCATION FILTERS')
for lid, tags in loc_tags.items():
    for tag in tags:
        sql.append(f"INSERT INTO location_filters (location_id, filter_id) VALUES ({lid}, {tag});")
sql.append('')

sql.append('-- EVENT FILTERS')
for eid, tags in event_tags.items():
    for tag in tags:
        sql.append(f"INSERT INTO event_filters (event_id, filter_id) VALUES ({eid}, {tag});")
sql.append('')

sql.append('-- USER FILTERS')
users = [1, 2, 3]
for uid in users:
    random_tags = random.sample(range(1, 238), 4)
    for tag in random_tags:
         sql.append(f"INSERT INTO user_filters (user_id, filter_id) VALUES ({uid}, {tag});")

with open('seed_data.sql', 'w', encoding='utf-8') as f:
    f.write('\n'.join(sql))

print('Wrote seed_data.sql')
