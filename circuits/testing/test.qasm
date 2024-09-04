OPENQASM 2.0;
include "qelib1.inc";
gate rzx(param0) q0,q1 { h q1; cx q0,q1; rz(param0) q1; cx q0,q1; h q1; }
gate ecr q0,q1 { rzx(pi/4) q0,q1; x q0; rzx(-pi/4) q0,q1; }
qreg q[127];
creg c[2];



rz(-pi) q[39];
sx q[39];
rz(-pi) q[39];
rz(pi/2) q[40];
sx q[40];
ecr q[40],q[39];
x q[40];
barrier q[40],q[39];
measure q[40] -> c[0];
measure q[39] -> c[1];