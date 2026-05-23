import json

with open(r'c:\Users\stefa\Desktop\Facultate\SEM2\Ingineria programarii\Proiect\socially-backend-ai\api\resources\filters.txt', 'r', encoding='utf-8') as f:
    filters = [line.strip() for line in f if line.strip()]

sql = []
sql.append('-- ==========================================================')
sql.append('-- ATENTIE: Acest script va sterge TOATE asocierile curente')
sql.append('-- ale filtrelor cu utilizatorii, locatiile si evenimentele!')
sql.append('-- ==========================================================')
sql.append('')
sql.append('SET FOREIGN_KEY_CHECKS = 0;')
sql.append('DELETE FROM user_filters;')
sql.append('DELETE FROM location_filters;')
sql.append('DELETE FROM event_filters;')
sql.append('DELETE FROM filters;')
sql.append('SET FOREIGN_KEY_CHECKS = 1;')
sql.append('')
sql.append('INSERT INTO filters (id, name) VALUES')

values = []
for i, f in enumerate(filters, start=1):
    # Escape single quotes in SQL by doubling them (e.g. Children''s menu)
    escaped = f.replace("'", "''")
    values.append(f"    ({i}, '{escaped}')")
    
sql.append(',\n'.join(values) + ';')

with open('reset_filters.sql', 'w', encoding='utf-8') as f:
    f.write('\n'.join(sql))

print('Wrote reset_filters.sql with', len(filters), 'inserts.')
