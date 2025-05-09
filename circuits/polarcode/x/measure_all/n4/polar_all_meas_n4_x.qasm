OPENQASM 2.0;
include "qelib1.inc";
qreg q[24];
creg c[40];
h q[2];
cx q[2],q[0];
cx q[2],q[3];
h q[2];
measure q[2] -> c[0];
reset q[2];
h q[5];
cx q[5],q[1];
cx q[5],q[4];
h q[5];
measure q[5] -> c[1];
reset q[5];
h q[8];
cx q[8],q[6];
cx q[8],q[9];
h q[8];
measure q[8] -> c[2];
reset q[8];
h q[11];
cx q[11],q[7];
cx q[11],q[10];
h q[11];
measure q[11] -> c[3];
reset q[11];
cx q[0],q[2];
cx q[6],q[2];
measure q[2] -> c[8];
reset q[2];
cx q[1],q[5];
cx q[7],q[5];
measure q[5] -> c[9];
reset q[5];
cx q[3],q[8];
cx q[9],q[8];
measure q[8] -> c[10];
reset q[8];
cx q[4],q[11];
cx q[10],q[11];
measure q[11] -> c[11];
reset q[11];
h q[14];
cx q[14],q[12];
cx q[14],q[15];
h q[14];
measure q[14] -> c[4];
reset q[14];
h q[17];
cx q[17],q[13];
cx q[17],q[16];
h q[17];
measure q[17] -> c[5];
reset q[17];
h q[20];
cx q[20],q[18];
cx q[20],q[21];
h q[20];
measure q[20] -> c[6];
reset q[20];
h q[23];
cx q[23],q[19];
cx q[23],q[22];
h q[23];
measure q[23] -> c[7];
reset q[23];
cx q[12],q[14];
cx q[18],q[14];
measure q[14] -> c[12];
reset q[14];
cx q[13],q[17];
cx q[19],q[17];
measure q[17] -> c[13];
reset q[17];
cx q[15],q[20];
cx q[21],q[20];
measure q[20] -> c[14];
reset q[20];
cx q[16],q[23];
cx q[22],q[23];
measure q[23] -> c[15];
h q[2];
cx q[2],q[0];
cx q[2],q[12];
h q[2];
measure q[2] -> c[16];
h q[5];
cx q[5],q[1];
cx q[5],q[13];
h q[5];
measure q[5] -> c[17];
h q[8];
cx q[8],q[3];
cx q[8],q[15];
h q[8];
measure q[8] -> c[18];
reset q[8];
h q[11];
cx q[11],q[4];
cx q[11],q[16];
h q[11];
measure q[11] -> c[19];
h q[14];
cx q[14],q[6];
cx q[14],q[18];
h q[14];
measure q[14] -> c[20];
h q[17];
cx q[17],q[7];
cx q[17],q[19];
h q[17];
measure q[17] -> c[21];
h q[20];
cx q[20],q[9];
cx q[20],q[21];
h q[20];
measure q[20] -> c[22];
h q[23];
cx q[23],q[10];
cx q[23],q[22];
h q[23];
measure q[23] -> c[23];
h q[0];
h q[1];
h q[3];
h q[4];
h q[6];
h q[7];
h q[9];
h q[10];
h q[12];
h q[13];
h q[15];
h q[16];
h q[18];
h q[19];
h q[21];
h q[22];
measure q[0] -> c[24];
measure q[1] -> c[25];
measure q[3] -> c[26];
measure q[4] -> c[27];
measure q[6] -> c[28];
measure q[7] -> c[29];
measure q[9] -> c[30];
measure q[10] -> c[31];
measure q[12] -> c[32];
measure q[13] -> c[33];
measure q[15] -> c[34];
measure q[16] -> c[35];
measure q[18] -> c[36];
measure q[19] -> c[37];
measure q[21] -> c[38];
measure q[22] -> c[39];