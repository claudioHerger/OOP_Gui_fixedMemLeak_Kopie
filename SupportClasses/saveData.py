from datetime import datetime
import os
import numpy as np

def get_directory_paths(start_time, tab_idx, components=None):
    today = datetime.now()
    day = today.strftime('%A')
    day_nr = today.day
    month = today.strftime('%b')
    year = today.strftime('%Y')
    hour = today.strftime('%H')
    minute = today.strftime('%M')

    date_dir = day + "_" + str(day_nr) + "_" + month +"_" +year
    final_dir = "starttime_"+str(start_time)+"_tab"+str(tab_idx+1)+"_created_at_"+str(hour)+"h_"+str(minute)+"min"

    if components is not None:
        final_dir = str(components)+"/starttime_"+str(start_time)+"_tab"+str(tab_idx+1)+"_created_at_"+str(hour)+"min"

    return date_dir, final_dir

def get_final_path(base_dir, date_dir, result_type, final_dir, data_file):
    data_file = os.path.splitext(os.path.basename(data_file))[0]
    full_path_to_final_dir = base_dir+'/DataFiles/ResultData/'+data_file+"/"+date_dir+result_type+final_dir

    return full_path_to_final_dir

def make_log_file(final_dir, **kwargs):
    today = datetime.now()

    with open(final_dir+"/logfile.txt", "a") as myfile:
        myfile.write(today.strftime("%a %d %b %H:%M:%S %Y")+"\n")

        for (kw,arg) in kwargs.items():
            myfile.write(kw+": " +str(arg)+"\n")

    return None

def save_result_data(final_dir, data_dict):
    for kw,arg in data_dict.items():
        if kw in ["DAS", "U_matrix", "VT_matrix", "retained_left_SVs"] :
            np.savetxt(final_dir+"/"+kw+".txt", arg, delimiter = '\t', fmt='%.7e')
        else:
            with open(final_dir+"/"+kw+".txt", "a") as myfile:
                # myfile.write(kw+":\n") if i wanted a header in each file
                myfile.write(str(arg))

    return None

def get_data_matrix_formatted(data, time_delays, wavelengths):
    """
    saves the input data matrix, time_delay and wavelength array in the same format as data_full_0.txt
    """
    nr_of_rows = len(time_delays) + 1
    nr_of_columns = len(wavelengths) + 1

    complete_data_matrix = np.zeros((nr_of_rows, nr_of_columns))

    complete_data_matrix[0,0] = 0.0
    complete_data_matrix[0,1:] = wavelengths
    complete_data_matrix[1:,0] = time_delays
    complete_data_matrix[1:,1:] = data

    return complete_data_matrix

def save_formatted_data_matrix_after_time(final_dir, time_delays, wavelengths, data_matrices_dict):
    for matrix_name, matrix in data_matrices_dict.items():
        formatted_matrix = get_data_matrix_formatted(matrix, time_delays, wavelengths)
        np.savetxt(final_dir+"/"+matrix_name+".txt", formatted_matrix, delimiter = '\t', fmt='%.7e')

    return None
