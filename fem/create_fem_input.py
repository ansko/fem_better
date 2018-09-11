def create_fem_input(Lx, moduli, input_fname, axis, task_name_template,
        mesh_fname='mesh.xdr', materials_fname='materials.bin'):

    """
    Creates the input script for FEMMain3 (ternary executable) that
    specifies the task with the tension along single axis.

    Parameters:
        Lx                  the size of the cubic box
        moduli              elastic moduli of the components in the next order:
                                [E_filler, E_interface, E_matrix]
        input_fname         the name of the file that will be written
        axis                the axis along which the strain is applied; one of
                                ['XX', 'YY', 'ZZ']

        task_name_template  template used in output fname
                                as ('{0}_{1}'.format(task_name, axis)
        mesh_fname          the name of the mesh file (fixed in FEMMain)
        materials_fname     the name of the file with materials elastoc constants
                                (fixed in FEMMain)
    """

    strains = {
        'XX': '0.01 0 0\n0 0 0\n0 0 0',
        'YY': '0 0 0\n0 0.01 0\n0 0 0',
        'ZZ': '0 0 0\n0 0 0\n0 0 0.01'
    }
    with open(input_fname, 'w') as fem_input:
        fem_input.write('\n'.join([
            'SizeX {0}'.format(Lx),
            'SizeY {0}'.format(Lx),
            'SizeZ {0}'.format(Lx),
            'MeshFileName {0}'.format(mesh_fname),
            'MaterialsGlobalFileName {0}'.format(materials_fname),
            'TaskName {0}{1}'.format(task_name_template, axis),
            'G_filler {0}\n'.format(moduli[0])]))
        if len(moduli) == 3: # ternary
            fem_input.write('\n'.join([
                'G_interface {0}'.format(moduli[1]),
                'G_matrix {0}'.format(moduli[2]),
                'Strain', strains[axis]
        ]))
        elif len(moduli) == 2:
            fem_input.write('\n'.join([
                'G_matrix {0}'.format(moduli[1]),
                'Strain', strains[axis]
        ]))
    return True


if __name__ =='__main__':
    def test_create_fem_input():
        Lx = 10
        moduli = [1, 1, 1]
        input_fname = 'test_fem_input.txt'
        axis = 'YY'
        create_fem_input(Lx, moduli, input_fname, axis)

    test_create_fem_input() # ok
