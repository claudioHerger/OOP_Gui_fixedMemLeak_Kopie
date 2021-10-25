import os
import numpy as np

def get_wavelengths_as_array(filename):
    with open(filename, 'r') as file:
        file.readline()
        data = [x.replace('\n', '') for x in file]

    data = np.array(data)

    return data

def get_timesteps_as_array(filename):
    with open(filename, 'r') as file:
        file.readline()
        data = [x.replace('\n', '') for x in file]

    data = np.array(data)

    return data

def get_data_as_array(filename):
    with open(filename, 'r') as file:
        file.readline()
        data = [x.replace('\n', '').split() for x in file]

    data = np.array(data)

    # convert the data into an easier to handle format
    for row in range(data.shape[0]):
        for col in range(data.shape[1]):
            data[row, col] = float(data[row, col])

    return data

def save_complete_data_matrix(timesteps, wavelengths, data_matrix_without):
    nr_of_wavelengths = len(wavelengths)
    nr_of_timesteps = len(timesteps)

    completed_matrix = np.zeros((nr_of_timesteps+1, nr_of_wavelengths+1))
    completed_matrix[0, 0] = 0
    completed_matrix[1:, 0] = timesteps
    completed_matrix[0, 1:] = wavelengths
    completed_matrix[1:, 1:] = data_matrix_without

    np.savetxt(os.getcwd()+"/DataFiles/maryam2.txt", completed_matrix, delimiter = '\t')

def save_some_data_matrix(timesteps, wavelengths, data_matrix_without):
    nr_of_neglected_wavelengths = 520
    nr_of_wavelengths = len(wavelengths) - nr_of_neglected_wavelengths
    nr_of_timesteps = len(timesteps)

    completed_matrix = np.zeros((nr_of_timesteps+1, nr_of_wavelengths+1))
    completed_matrix[0, 0] = 0
    completed_matrix[1:, 0] = timesteps
    completed_matrix[0, 1:] = wavelengths[0:len(wavelengths)-nr_of_neglected_wavelengths]
    completed_matrix[1:, 1:] = data_matrix_without[:, 0:len(wavelengths)-nr_of_neglected_wavelengths]

    np.savetxt(os.getcwd()+"/DataFiles/maryam2_reduced.txt", completed_matrix, delimiter = '\t')


if __name__ == "__main__":

    wavelengths_filename = "DataFiles/maryam2/wl_svd.txt"
    timesteps_filename = "DataFiles/maryam2/delays_sh_c.txt"
    data_filename = "DataFiles/maryam2/Ru_bpy2phen_svd_cl.txt"

    wavelengths = get_wavelengths_as_array(wavelengths_filename)
    timesteps = get_timesteps_as_array(timesteps_filename)
    data_without_timesteps_or_wavelengths = get_data_as_array(data_filename)


    save_complete_data_matrix(timesteps, wavelengths, data_without_timesteps_or_wavelengths)