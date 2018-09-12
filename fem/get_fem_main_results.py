def get_fem_main_results(fname, axis):
    """
    FEMMain performs tension along single axis and produces
    output file with some significant lines (lines indexing starts from 0):
        line 1:  filler_volume total_volume
        line 14: strains[9] stresses[9]

    This function reads the output file and returns data in the dict:
    {
        'fi_filler': ,
        'E': ,
    }

    Parameters:
        fname  the name of the produced file by FEMMain
        axis   the axis along which the strain was applied;
                   one of ['XX', 'YY', 'ZZ']
    """

    stresses_indices = {'XX': 9, 'YY': 13, 'ZZ': 17}
    strains_indices = {'XX': 0, 'YY': 4, 'ZZ': 8}
    with open(fname) as f:
        lines = f.read().split('\n')
    vol_filler = float(lines[1].split()[0])
    vol_total = float(lines[1].split()[1])
    stress = float(lines[14].split()[stresses_indices[axis]])
    strain = float(lines[14].split()[strains_indices[axis]])
    try:
        return {
            'fi_filler': vol_filler / vol_total,
            'E': stress / strain,
        }
    except ZeroDivisionError:
        return {}


if __name__ == '__main__':
    def test_get_fem_main_results():
        fname = 'test_elas_EXX_results.txt'
        axis = 'XX'
        data = get_fem_main_results(fname, axis)
        print(data)

    test_get_fem_main_results() # ok
