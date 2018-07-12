#!/usr/bin/python

## https://codeselfstudy.com/blog/how-to-calculate-standard-deviation-in-python/

import os

from pprint import pprint

BASE_DIR = "/home/zaca/devel/chsdn/shared"
FOLDER_BASE_NAME = "%snodes"
FILE_BASE_NAME = "nodes%s.log"

NODE_SET = [5, 10, 15]

# Open the file (read-only)
folder_name = FOLDER_BASE_NAME % "05"
file_name = FILE_BASE_NAME % "05"
file_path = os.path.join(BASE_DIR, folder_name, file_name)
file = open(file_path)
line = file.readline()
run_no = 0
data_group = []
iter_list = []
time_list = []
report = []
while line:
    if '#####' not in line:
        # linha de dados
        data = line.split(";")
        iter_list.append(int(data[5]))
        time_list.append(float(data[7]))
    if '#####' in line:
        # sumariza
        if iter_list:
            max_iter = max(iter_list)
        if time_list:
            max_time = max(time_list)
        # salva os dados do grupo
        report.append([max_iter, max_time])
        # inicia novo grupo
        iter_list = []
        time_list = []
    # read next line
    line = file.readline()
# close the file
file.close()
print report