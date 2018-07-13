#!/usr/bin/python

## Source: standard_deviation()
## https://codeselfstudy.com/blog/how-to-calculate-standard-deviation-in-python/

import os
from math import sqrt
from pprint import pprint


########################################
####  Script configuration          ####
########################################
BASE_DIR = "/home/zaca/Dropbox/UFRGS/CH_Selection/results"
FOLDER_BASE_NAME = "%snodes"
FILE_BASE_NAME = "nodes%s.log"
IPERF_BASE_NAME = "iperf_s_n%s_r%s"
NODE_SET = ["05", "10", "15", "20", "25", "30"]


########################################
####  Calculate Avg and Std Dev     ####
########################################
def standard_deviation(lst, population=False):
    """Calculates the standard deviation for a list of numbers."""
    num_items = len(lst)
    mean = sum(lst) / num_items
    differences = [x - mean for x in lst]
    sq_differences = [d ** 2 for d in differences]
    ssd = sum(sq_differences)

    # Note: it would be better to return a value and then print it outside
    # the function, but this is just a quick way to print out the values along
    # the way.
    if population is True:
        variance = ssd / num_items
    else:
        variance = ssd / (num_items - 1)
    std_dev = sqrt(variance)
    # The mean: mean
    # The differences: differnces
    # The sum of squared differences: ssd
    # The variance: variance
    # The standard deviation: std_dev
    return mean, std_dev


########################################
####  Extract Iperf Measures        ####
########################################
def lost_bytes(iperf_file_path=""):
    # Open the file
    iperf_file = open(iperf_file_path, 'r')
    data = iperf_file.readlines()
    iperf_file.close()
    # Extract data
    lost_datagrams = 0
    for i in range(len(data) -1, 0, -1):
        if data[i].count("Mbits/sec"):
            lost_datagrams = int(data[i].split(" ")[16].split("/")[0])
            break
    datagram_size = int(data[2].split(" ")[1])
    return int(lost_datagrams * datagram_size)


########################################
####         Main Function          ####
########################################
def get_stats(no_of_nodes = "05"):
    # Open the file (read-only)
    folder_name = FOLDER_BASE_NAME % no_of_nodes
    file_name = FILE_BASE_NAME % no_of_nodes
    file_path = os.path.join(BASE_DIR, folder_name, file_name)
    f = open(file_path)
    line = f.readline()
    run_no = 0
    iter_list = []
    time_list = []
    report = []
    while line:
        if '#####' not in line:
            # data line
            data = line.split(";")
            iter_list.append(int(data[5]))
            time_list.append(float(data[7]))
        if '#####' in line:
            # summarize
            if iter_list and time_list:
                max_iter = max(iter_list)
                max_time = max(time_list)
                # increment the run_number
                run_no = run_no + 1
                # get lost bytes from iperf
                iperf_file_name = IPERF_BASE_NAME % (no_of_nodes, str(run_no).zfill(2))
                iperf_path = os.path.join(BASE_DIR, folder_name, iperf_file_name)
                lost_data = lost_bytes(iperf_path)
                # salva os dados do grupo
                report.append([run_no, max_iter, max_time, lost_data])
            # inicia novo grupo
            iter_list = []
            time_list = []
        # read next line
        line = f.readline()
    # Add the result of the last group
    # sumariza
    if iter_list and time_list:
        max_iter = max(iter_list)
        max_time = max(time_list)
        # increment the run_number
        run_no = run_no + 1
        # get lost bytes from iperf
        iperf_file_name = IPERF_BASE_NAME % (no_of_nodes, str(run_no))
        iperf_path = os.path.join(BASE_DIR, folder_name, iperf_file_name)
        lost_data = lost_bytes(iperf_path)
        # salva os dados do grupo
        report.append([run_no, max_iter, max_time, lost_data])
    # close the file
    f.close()
    # separate measures in arrays
    rounds_arr = ([ rounds_elect for run, rounds_elect, max_time, bytes_lost in report ])
    time_arr = ([ max_time for run, rounds_elect, max_time, bytes_lost in report ])
    lost_arr = ([ bytes_lost for run, rounds_elect, max_time, bytes_lost in report ])
    # process the stats
    round_avg, round_sd = standard_deviation(rounds_arr)
    time_avg, time_sd = standard_deviation(time_arr)
    lost_avg, lost_sd = standard_deviation(lost_arr)
    
    # NodeNo  -- rounds(avg, sd) -- time(avg, sd) -- lost (avg, sd)
    print "%i \t %.6f \t %.6f \t %.6f \t %.6f \t %.2f \t %.6f" % (
        int(no_of_nodes), 
        round_avg, round_sd, 
        time_avg, time_sd, 
        lost_avg, lost_sd)

if __name__ == '__main__':
    for node in NODE_SET:
        get_stats(node)