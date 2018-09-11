def process_structure_log(strucutre_log_fname):
    processed = dict()
    with open(strucutre_log_fname) as f:
        lines = f.read().split('\n')
    for line in lines:
        if line.endswith('(algorithm used)'):
            processed['algorithm'] = line.split()[0]
        if line.endswith('(status of system formation)'):
            processed['status'] = int(line.split()[0])
        if line.endswith('(number of fillers prepared)'):
            processed['N_real'] = int(line.split()[0])
        if line.endswith('(requested number of fillers)'):
            processed['N_requested'] = int(line.split()[0])
        if line.endswith('(possible max attempts number)'):
            processed['max_attempts'] = int(line.split()[0])
        if line.endswith('(real attempts number)'):
            processed['attempts_made'] = int(line.split()[0])
        if line.endswith('(flag_testing == is system ok)'):
            processed['testing'] = int(line.split()[0])
        if line.endswith('(number of intersections in system)'):
            processed['intersections'] = int(line.split()[0])
        if line.endswith('(percolation flag along x: )'):
            processed['perc_x'] = int(line.split()[0])
        if line.endswith('(percolation flag along y: )'):
            processed['perc_y'] = int(line.split()[0])
        if line.endswith('(percolation flag along z: )'):
            processed['perc_z'] = int(line.split()[0])
    return processed
