import numpy as np
from pathlib import Path
from . import __tools as tls
from . import __polarcodec as codec
from .__qpolarprep import q1prep as q1prep
import time
from qiskit import QuantumCircuit

# from here is to calculate the preparation rate and logical error rate

def get_q1prep_sr(n, lstate, results):
    # n = 4       # number of polarization steps (polar code length N = 2^n)
    # lstate = "X" # prepared logical state: may be "Z" (|0>) or "X" (|+>)
    
    # # measurement results file
    # # each line in the file contains the measurement results for one preparation experiment
    # mfile = 'polar_code_n{}_{}_simulator.txt'.format(n, lstate.lower())
    
    # zpos: last position frozen in zero, counting from zero! (0 <= zpos < N-1)
    # list of zpos values, assuming that logical |0> is prepared (lstate = "Z")
    #       n =   0   1   2  3  4  5   6   7   8   9   10 
    zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]

    if lstate == "Z":
        # |0> is prepared: take zpos value from the list above
        zpos = zpos_list[n]
    elif lstate == "X":
        # |+> is prepared: zpos value from the list above -1
        zpos = zpos_list[n] -1
    else:
        raise TypeError("Illegal 'lstate' value")

    N     = 2**n     # polar code length
    mnum  = n*(N//2) # number of measurement results for each state preparation

    count_success = 0    # number of valid measurement results
    count_failure = 0    # number of invalid measurement results
    total_shots = sum(results.values())

    # ##################################################################
    # read measurement results from file, and check which ones are valid
    # ##################################################################
    for line, meas_counts in results.items():
        # print(line)
        # remove spaces at beginning and end of line
        mstr = line.strip()

        # init the measurement results array -- of length len(mstr)
        meas = np.zeros((len(mstr),), dtype=int) 

        # convert from string to np array
        for i in range(0, len(mstr)):
            meas[i] = ord(mstr[i]) - ord('0')	
            if meas[i] != 0 and meas[i] != 1:
                raise TypeError("Illegal measurement result: must be 0 or 1")


        # check if 'meas' are valid measurement results
        success, qstate_UV = q1prep(n, zpos, meas)
        if success == 1:
            count_success = count_success + meas_counts
            # print(meas)
        else:
            count_failure = count_failure + meas_counts

    # print("  number of valid measurement results = ", count_success, count_success / total_shots)
    # print("number of invalid measurement results = ", count_failure, count_failure / total_shots)
    # print("")

    return count_success / total_shots

def get_logical_error_on_accepted_states(n, lstate, results):
    # n = 4       # number of polarization steps (polar code length N = 2^n)
    # lstate = "X" # prepared logical state: may be "Z" (|0>) or "X" (|+>)
    
    # # measurement results file
    # # each line in the file contains the measurement results for one preparation experiment
    # mfile = 'polar_code_n{}_{}_simulator.txt'.format(n, lstate.lower())
    
    # zpos: last position frozen in zero, counting from zero! (0 <= zpos < N-1)
    # list of zpos values, assuming that logical |0> is prepared (lstate = "Z")
    #       n =   0   1   2  3  4  5   6   7   8   9   10 
    zpos_list = [-1, -1, 1, 3, 6, 7, 22, 15, 90, 31, 362]

    if lstate == "Z":
        # |0> is prepared: take zpos value from the list above
        zpos = zpos_list[n]
    elif lstate == "X":
        # |+> is prepared: zpos value from the list above -1
        zpos = zpos_list[n] -1
    else:
        raise TypeError("Illegal 'lstate' value")

    N     = 2**n     # polar code length
    mnum  = n*(N//2) # number of measurement results for each state preparation

    # count_discard/accept: number of states discarded/accepted during the state preparation protocol
    # in case of errors detected during state preparation, the state is discarded, otherwise it is accepted  
    count_accept  = 0    # number of accepted states (valid measurement results) -- was count_success in previous version
    count_discard = 0    # number of discarded states (invalid measurement results) -- was count_failure in previous version

    # count_logerror: number of logical errors on the accepted states
    # we check whether the undetected errors that may have survived on the accepted (prepared)  
    # state can be successfully corrected or not. when not, a logical error is counted
    count_logerror = 0 
    count_undecided = 0

    # This is repeating just for calculating the detection time
    tmp_start_time  = time.perf_counter()
    for line, meas_counts in results.items():
        # print(line)
        # remove spaces at beginning and end of line
        mstr = line.strip()

        # init the measurement results array -- of length len(mstr)
        meas = np.zeros((len(mstr),), dtype=int) 

        # convert from string to np array
        for i in range(0, len(mstr)):
            meas[i] = ord(mstr[i]) - ord('0')	
            if meas[i] != 0 and meas[i] != 1:
                raise TypeError("Illegal measurement result: must be 0 or 1")


        # check if 'meas' are valid measurement results
        success, qstate_UV = q1prep(n, zpos, meas[:N-1:-1])
        if success == 1:
            pass
        else:
            pass

    tmp_end_time = time.perf_counter()
    detection_time = tmp_end_time - tmp_start_time

    total_shots = sum(results.values())


    tmp_start_time  = time.perf_counter()
    # print("Total shots :", total_shots)
    # ##################################################################
    # read measurement results from file, and check which ones are valid
    # ##################################################################
    for line, meas_counts in results.items():
        # print(line)
        # remove spaces at beginning and end of line
        mstr = line.strip()

        # init the measurement results array -- of length len(mstr)
        meas = np.zeros((len(mstr),), dtype=int) 

        # convert from string to np array
        for i in range(0, len(mstr)):
            meas[i] = ord(mstr[i]) - ord('0')	
            if meas[i] != 0 and meas[i] != 1:
                raise TypeError("Illegal measurement result: must be 0 or 1")


        # check if 'meas' are valid measurement results
        success, qstate_UV = q1prep(n, zpos, meas[:N-1:-1])
        if success == 1:
            count_accept = count_accept + meas_counts
            # print(meas)
        else:
            count_discard = count_discard + meas_counts

        if success == 1:
            # ###############################################################
            # this part is new with respect to previous version of the script
            # ###############################################################
            # we check whether the  undetected errors  that may have survived on 
            # the accepted (prepared) state can be successfully corrected or not 
            
            if lstate.lower() == "z":    
                # |0> is prepared: logical information encoded at position zpos
                
                # qstate_U: the U part of qstate_UV 
                qstate_U = np.zeros((N,), dtype=int)
                qstate_U[:zpos] = qstate_UV[:zpos]
                
                # encode qstate_U -- encoding is done in place
                codec.polarenc(qstate_U)
                
                # add measurement resuts (data qubits, measured after state preparation)
                # print(meas[N-1::-1], meas[N-1:])
                qstate_U = np.mod(qstate_U + meas[N-1::-1], 2)
                
                # run polar decoder (logical information encoded at position zpos)
                # print(1-2*qstate_U, qstate_U)
                u_ipos = codec.polardec(1-2*qstate_U, zpos)
                
                if u_ipos == -1:
                    # undecided value (llr = 0): we count half an error, since a 
                    # random choice would give an error with probability 1/2
                    count_logerror = count_logerror + (0.5 * meas_counts); # count 1/2 logical error
                elif u_ipos != qstate_UV[zpos]:
                    # logical error (the decoded value is not the correct one)
                    count_logerror = count_logerror + (1 * meas_counts);   # count a logical error
                
            elif lstate.lower() == "x":  
                # |+> is prepared: logical information encoded at position zpos+1
                
                # qstate_V: the V part of qstate_UV 
                qstate_V = np.zeros((N,), dtype=int)
                qstate_V[zpos+2:] = qstate_UV[zpos+2:]
                
                # encode qstate_V -- encoding is done in place
                codec.revpolarenc(qstate_V)
                
                # add measurement resuts (data qubits, measured after state preparation)
                # print(meas[N-1::-1], (meas[N-1::-1])[::-1])
                logical_bit = meas[N-1::-1]
                # logical_bit = (meas[N-1::-1])[::-1]
                qstate_V = np.mod(qstate_V + logical_bit, 2)
                
                # run polar decoder (logical information encoded at position zpos+1)
                # print(1-2*qstate_V, qstate_V)
                v_ipos = codec.revpolardec(1-2*qstate_V, zpos+1)
                
                if v_ipos == -1:
                    # undecided value (llr = 0): we count half an error, since a 
                    # random choice would give an error with probability 1/2
                    count_logerror = count_logerror+0.5; # count 1/2 logical error
                    count_undecided = count_undecided + 1; 
                    # print(" undecided ... ")
                elif v_ipos != qstate_UV[zpos+1]:
                    # logical error (the decoded value is not the correct one)
                    count_logerror = count_logerror+1;   # count a logical error
            
            else:
                raise TypeError("Illegal 'lstate' value")
            
    tmp_end_time = time.perf_counter()
    decoding_time = tmp_end_time - tmp_start_time - detection_time

    # print("number of discarded states (invalid measurement results) = ", count_discard)
    # print(" number of accepted states   (valid measurement results) = ", count_accept)
    # print("        number of logical errors on the accepted states  = ", round(count_logerror))

    fidelity = 0
    if count_accept > 0:
        fidelity = ((count_accept - round(count_logerror)) / count_accept)

    return count_accept, round(count_logerror), count_undecided, fidelity, detection_time, decoding_time



# from here is the function to generate the state preparation of quantum polar code circuit
def divide_half_list(lst):
    # print("function:", lst, int(len(lst)//2))
    idx = int(len(lst)//2)
    firsthalf = lst[:idx]
    secondhalf = lst[idx:]

    return firsthalf, secondhalf

def make_polar_qc_based_p1(n):
    qr = 2**n
    total_qubit = qr 

    cr = total_qubit 
    
    qc = QuantumCircuit(total_qubit, cr)

    return qc

def generate_polar_encoding(qc, n, s, n_bit):
    # print(n, s)
    if n == 1:
        if (n_bit[n-1] == "0"):
            qc.cx(s[1], s[0])
        else:
            qc.cx(s[0], s[1])

        # print(n, n_bit[n-1], n_bit)
    else:
        s1, s2 = divide_half_list(s)
        # print(s1, s2)
        qc = generate_polar_encoding(qc, n-1, s1, n_bit)         
        qc = generate_polar_encoding(qc, n-1, s2, n_bit)

        for i in range(len(s1)):
            if (n_bit[n-1] == "0"):
                qc.cx(s2[i], s1[i])
            else:
                qc.cx(s1[i], s2[i])
            

        # print(n, n_bit[n-1], n_bit)
    
                
    return qc
    
def make_polar_qc_based_p2(n, meas_data=False):
    qr = 2**n
    ar = 2**(n-1)

    total_qubit = qr + ar

    if meas_data:
        cr = total_qubit + (ar * (n-1))
    else:
        cr = (ar * (n)) 
    
    qc = QuantumCircuit(total_qubit, cr)

    return qc

def check_has_zero(n_bit):
    has_zero = False
    # print(n_bit)
    for i in range(1, len(n_bit)):
        if n_bit[i - 1] == '0':
            has_zero = True

    return has_zero
    
def generate_polar_encoding_measurement(qc, n, s, a, m, n_bit):
    if n == 1:
        if (n_bit[n-1] == "1"):
            # print("Skip first ZZ measurement")
            pass
            # if started with Z measurement, skip it
        
            # qc.cx(s[0], a[0])
            # qc.cx(s[1], a[0])
            # qc.measure(a[0], m[0])
            # m.pop(0)
            # qc.reset(a[0])
        else:
            qc.h(a[0])
            qc.cx(a[0], s[0])
            qc.cx(a[0], s[1])
            qc.h(a[0])
            qc.measure(a[0], m[0])
            
            # with qc.if_test((m[0], 1)):
            #     qc.x(a[0])
                
            m.pop(0)
            
            qc.reset(a[0])
            
        # print(n, n_bit[n-1], n_bit)
    else:
        s1, s2 = divide_half_list(s)
        a1, a2 = divide_half_list(a)
        
        # print(s1, s1[-1], s2, s2[-1], n_bit, n, n_bit[n-1])
        qc = generate_polar_encoding_measurement(qc, n-1, s1, a1, m, n_bit)         
        qc = generate_polar_encoding_measurement(qc, n-1, s2, a2, m, n_bit)
        
        # print(n, s, n_bit[n-1], len(s1))
        # for i in range(len(s1) - (2**(n-2)) ):
        # print("--------")
        for i in range(len(s1)):
            if (n_bit[n-1] == "1"):
                # print("--- 1 ---")
                # print(idx, i, s, s1, s2, " --- ", a, ": ", s1[i], s2[i])
                if check_has_zero(n_bit[:n]):
                    idx_meas = a[i]
                    # print(idx_meas, n, i, m)
                    qc.cx(s1[i], idx_meas)
                    qc.cx(s2[i], idx_meas)
                    qc.measure(idx_meas, m[0])
                    # with qc.if_test((m[0], 1)):
                    #         qc.x(idx_meas)
                    m.pop(0)
                    qc.reset(idx_meas)
                    
                else:
                    pass
                    # print("Skip ZZ Measurement", n-1, n_bit[n-1], n_bit[:n])
            else:      
                # print(idx, i, s, s1, s2, " --- ", a, ": ", s1[i], s2[i])
                idx_meas = a[i] 
                # print(idx_meas, n, i, m)
                qc.h(idx_meas)
                qc.cx(idx_meas, s1[i])
                qc.cx(idx_meas, s2[i])
                qc.h(idx_meas)
                qc.measure(idx_meas, m[0])
                # with qc.if_test((m[0], 1)):
                #             qc.x(idx_meas)
                m.pop(0)
                qc.reset(idx_meas)    
                
                
    return qc

def get_i_position(n):
    i = 0

    if n == 2:
        i = 2
    elif n == 3:
        i = 4
    elif n == 4:
        i = 7
    elif n == 5:
        i = 8
    elif n == 6:
        i = 23
    elif n == 7:
        i = 16
    
    return i

def polar_code_p2(n, meas_data=False, base="z", add_barrier=False):
    bit_format = "0:0{}b".format(n)
    bit_format = "{" + bit_format + "}"
    # bit_format = "{0:04b}"
    # print(bit_format)

    if base == "z":
        i = get_i_position(n)
    else:
        i = get_i_position(n) - 1
    
    n_bit = bit_format.format(i-1)[::-1]
    # n_bit = bit_format.format(n-1)
    print("n =", n, ", b =", "{} ({})".format(n_bit, i-1), ", i =", i)
    
    qc=make_polar_qc_based_p2(n, meas_data)
    # s=range(2**n + 2**(n-1))
    
    s=[]
    a=[]
    m=[]
    j = 0
    for i in range(qc.num_qubits):
        if j == 2:
            a.append(i)
            j = -1
        else:
            s.append(i)
            
        j = j + 1
    
    for k in range(0, qc.num_clbits):
        m.append(k)
    
    # print(s, a, m)

    # NOTE THAT the measurement order for n >= 6 is not fixed yet.
    
    if base == "x":
        if meas_data==False:
            if n == 3:
                m = [0,1,4,5,2,3,6,7,8,9,10,11]
            elif n == 4:
                m = [0,1,2,3,8,9,10,11,4,5,6,7,12,13,14,15,16,17,18,19,20,21,22,23]
            elif n == 5:
                m = [0, 1, 16, 17, 2, 3, 18, 19, 32, 33, 34, 35, 4, 5, 20, 21, 6, 7, 22, 23, 36, 37, 38, 39, 
                     48, 49, 50, 51, 52, 53, 54, 55, 8, 9, 24, 25, 10, 11, 26, 27, 40, 41, 42, 43, 12, 13, 28, 29, 14, 15, 30, 
                     31, 44, 45, 46, 47, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 
                     76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 
                     101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111]
        else:
            if n == 3:
                m = [0,1,4,5,2,3,6,7,8,9,10,11, 12, 13, 14, 15, 16, 17, 18, 19]
            elif n == 4:
                m = [0,1,2,3,8,9,10,11,4,5,6,7,12,13,14,15,16,17,18,19,20,21,22,23,24, 25, 
                     26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47]
            elif n == 5:
                m = [0, 1, 16, 17, 2, 3, 18, 19, 32, 33, 34, 35, 4, 5, 20, 21, 6, 7, 22, 23, 36, 37, 38, 39, 
                     48, 49, 50, 51, 52, 53, 54, 55, 8, 9, 24, 25, 10, 11, 26, 27, 40, 41, 42, 43, 12, 13, 28, 29, 14, 15, 30, 
                     31, 44, 45, 46, 47, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 
                     76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 
                     101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111]
    else:
        if meas_data==False:
            if n == 3:
                m = [0,1,2,3]
            elif n == 4:
                m = [0,1,8,9,2,3,10,11,16,17,18,19,4,5,12,13,6,7,14,15,20,21,22,23,24,25,26,27,28,29,30,31]
            elif n == 5:
                m = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 
                     26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 
                     51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 
                     76, 77, 78, 79]    
        else:
            if n == 3:
                m = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
            elif n == 4:
                m = [0,1,8,9,2,3,10,11,16,17,18,19,4,5,12,13,6,7,14,15,20,21,22,23,24,25,
                     26,27,28,29,30,31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47]
            elif n == 5:
                m = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 
                     26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 
                     51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 
                     76, 77, 78, 79]  

    # print(m)
    
    qc = generate_polar_encoding_measurement(qc, n, s, a, m, n_bit)

    if meas_data:

        if add_barrier:
            qc.barrier(range(qc.num_qubits))

        for i in s:
            if base == "x":
                qc.h(i)

            qc.measure(i,m[0])
            m.pop(0)

    return qc

