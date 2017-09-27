# -*- coding: utf-8 -*-

import csv
import chardet
import sqlite3


def generate_csv_preview(file_path, rows):
    """
    生成csv文件预览
    :param file_path: 
    :param rows: 
    :return: 
    """
    preview = []
    try:
        with open(file_path, 'rb') as f:
            data = f.readline() + f.readline()
            encoding = chardet.detect(data).get('encoding')
        with open(file_path, 'rb') as f:
            reader = csv.reader(f)
            cnt = 0
            for row in reader:
                preview.append([s.decode(encoding) for s in row])
                cnt += 1
                if cnt > rows:
                    break
    finally:
        return preview


def generate_sqlite_preview(file_path, rows):
    """
    生成sqlite数据库预览
    :param file_path: 
    :param rows: 
    :return: 
    """
    preview = {
        'db': [['Table', 'Total Rows', 'Total Columns', 'Columns']],
        'tables': {}
    }
    try:
        conn = sqlite3.connect(file_path)
        c = conn.cursor()

        c.execute('SELECT name FROM sqlite_master WHERE type = "table"')
        tables = [r[0] for r in c.fetchall()]
        for t in tables:
            c.execute('SELECT COUNT(*) FROM %s' % t)
            total_rows = c.fetchone()[0]
            c.execute('SELECT * FROM %s' % t)
            columns = [i[0] for i in c.description]
            total_columns = len(columns)
            preview['db'].append([t, total_rows, total_columns, ', '.join(columns)])
            preview['tables'][t] = [columns] + [list(r) for r in c.fetchmany(rows)]

        conn.close()
    finally:
        return preview
