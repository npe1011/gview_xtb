#!/usr/bin/python3
import os
import sys
import shutil
import subprocess

# XTB file name-related constants
XTB_COMMAND = 'xtb'
XTB_ENERGY_FILE = 'energy'
XTB_GRADIENT_FILE = 'gradient'
XTB_HESSIAN_FILE = 'hessian'


def read_hessian(hessian_file, num_atoms):
    """
    read hessian file by XTB and return 3 x ((3*NAtoms*(3*NAtoms+1))/6) list <float>
    :param hessian_file:
    :param num_atoms: number of atoms
    """
    with open(hessian_file, 'r') as f:
        hessian_data = f.readlines()

    assert hessian_data[0].strip().startswith('$hessian')

    hess_1d = []
    for line in hessian_data[1:]:
        if line.strip() == '':
            continue
        if line.strip().startswith('$end'):
            break
        hess_1d.extend([float(x) for x in line.strip().split()])

    assert len(hess_1d) == (num_atoms * 3) ** 2

    # 1d to NxN
    hessian = [hess_1d[i:i + num_atoms * 3] for i in range(0, len(hess_1d), num_atoms * 3)]

    # to gaussian format
    gaussian_hessian = []
    temp = []
    for i in range(num_atoms*3):
        for j in range(i+1):
            temp.append(hessian[i][j])
            if len(temp) == 3:
                gaussian_hessian.append(temp)
                temp = []
    return gaussian_hessian


def read_energy(energy_file):
    """
    return energy in float from energy_file
    """
    with open(energy_file, 'r') as f:
        energy_data = f.readlines()

    assert energy_data[0].strip().startswith('$energy')
    return float(energy_data[1].strip().split()[1])


def read_gradient(gradient_file, num_atoms):
    """
    read gradient file by XTB and return (num_atom)x(3) list <float>
    :param gradient_file:
    :param num_atoms: number of atoms
    """
    with open(gradient_file, 'r') as f:
        gradient_data = f.readlines()

    assert gradient_data[0].strip().startswith('$grad')

    gradient = []
    for line in gradient_data[2 + num_atoms:2 + 2 * num_atoms]:
        gradient.append([float(x) for x in line.strip().split()])

    return gradient


def main():
    # Gau_External layer InputFile OutputFile MsgFile FChkFile MatElFile
    # Gau_External can have several arguments like : script --option layer ...
    args = sys.argv
    input_file = args[-5]
    input_dir = os.path.dirname(os.path.abspath(args[-5]))  # input file directory (Gaussian scratch)
    output_file = args[-4]  # Output file read by Gaussian
    log_file = args[-3]  # Error messages are written.
    job_name = os.path.splitext(os.path.basename(input_file))[0]
    work_dir = os.path.join(input_dir, job_name + '_' + str(os.getpid()))
    additional_args = args[1:-5]

    # Read input
    with open(input_file, 'r') as f:
        input_row_data = f.readlines()
        
    #atoms  derivatives-requested  charge  multi
    num_atoms, derivatives_type, charge, multi = [int(x) for x in input_row_data[0].strip().split()] 

    # Run XTB in working directory
    os.mkdir(work_dir)
    shutil.copy(input_file, work_dir)
    os.chdir(work_dir)
    if derivatives_type < 2:
        xtb_commands = ['xtb', '--grad']
    else:
        xtb_commands = ['xtb', '--hess', '--grad']
    xtb_commands.extend(additional_args)
    charge = str(charge)
    spin = str(multi-1)
    xtb_commands.extend(['--chrg', charge, '--uhf', spin, input_file])

    subprocess.run(xtb_commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

    # check normal termination:
    if not (os.path.exists(XTB_ENERGY_FILE) and os.path.exists(XTB_GRADIENT_FILE)):
        os.chdir(input_dir)
        with open(log_file, 'w') as f:
            f.write('---------------------XTB ABNORMAL TERMINATION ERROR---------------------\n')
            f.write(xtb_log)
    
    # when normal termination
    else:           

        # Prepare output file for Gaussian
        output_data = []

        # energy, dipole-moment (xyz)	 	E, Dip(I), I=1,3	 	4D20.12
        energy = read_energy(XTB_ENERGY_FILE)
        output_data.append('{0:20.12e}{1:20.12e}{2:20.12e}{3:20.12e}\n'.format(energy, 0.0, 0.0, 0.0))

        # gradient on atom (xyz)	 	FX(J,I), J=1,3; I=1,NAtoms	 	3D20.12
        if derivatives_type >= 1:
            gradient = read_gradient(XTB_GRADIENT_FILE, num_atoms)
            for n in range(num_atoms):
                output_data.append('{0:20.12e}{1:20.12e}{2:20.12e}\n'.format(gradient[n][0], gradient[n][1], gradient[n][2]))

        # polarizability	 	Polar(I), I=1,6	 	3D20.12   (dummy)
        # dipole derivatives	 	DDip(I), I=1,9*NAtoms	 	3D20.12 (dummy)
        for n in range(3 * num_atoms + 2):
            output_data.append('{0:20.12e}{1:20.12e}{2:20.12e}\n'.format(0.0, 0.0, 0.0))

        # force constants	 	FFX(I), I=1,(3*NAtoms*(3*NAtoms+1))/2	 	3D20.12
        if derivatives_type == 2:
            gaussian_hessian = read_hessian(XTB_HESSIAN_FILE, num_atoms)
            for line in gaussian_hessian:
                output_data.append('{0:20.12e}{1:20.12e}{2:20.12e}\n'.format(line[0], line[1], line[2]))
        
        # Retrun to the input directory
        os.chdir(input_dir)

        # Prepare output file for Gaussian
        with open(output_file, 'w') as f:
            f.writelines(output_data)
        with open(log_file, 'w') as f:
            f.write('')

    # Clean-up
    shutil.rmtree(work_dir)


if __name__ == '__main__':
    main()
    
   