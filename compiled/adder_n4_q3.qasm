OPENQASM 2.0;
include "qelib1.inc";
gate rzx(param0) q0,q1 { h q1; cx q0,q1; rz(param0) q1; cx q0,q1; h q1; }
gate ecr q0,q1 { rzx(pi/4) q0,q1; x q0; rzx(-pi/4) q0,q1; }
qreg q[127];
creg c[4];
rz(-pi/2) q[87];
sx q[87];
rz(pi) q[87];
sx q[87];
rz(3*pi) q[87];
rz(pi/2) q[87];
sx q[87];
rz(3*pi/2) q[87];
sx q[87];
rz(5*pi/2) q[87];
rz(-pi/2) q[87];
sx q[87];
rz(pi) q[87];
sx q[87];
rz(3*pi) q[87];
rz(pi/2) q[87];
sx q[87];
rz(3*pi/2) q[87];
sx q[87];
rz(5*pi/2) q[87];
rz(pi/2) q[87];
rz(pi/2) q[87];
sx q[87];
rz(pi/2) q[87];
rz(pi/2) q[87];
rz(-3*pi/4) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(3*pi/2) q[93];
sx q[93];
rz(5*pi/2) q[93];
rz(-pi) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(-pi/2) q[93];
ecr q[93],q[87];
rz(-pi/2) q[87];
sx q[87];
rz(pi) q[87];
sx q[87];
rz(3*pi) q[87];
rz(pi/2) q[87];
sx q[87];
rz(3*pi/2) q[87];
sx q[87];
rz(5*pi/2) q[87];
rz(-pi/4) q[87];
sx q[87];
rz(pi) q[87];
sx q[87];
rz(3*pi) q[87];
rz(pi/2) q[87];
sx q[87];
rz(3*pi/2) q[87];
sx q[87];
rz(5*pi/2) q[87];
rz(pi/2) q[87];
rz(pi/2) q[87];
sx q[87];
rz(pi/2) q[87];
rz(pi/2) q[87];
x q[93];
rz(pi) q[93];
sx q[93];
rz(2*pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(-pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(3*pi/2) q[93];
sx q[93];
rz(5*pi/2) q[93];
rz(-pi) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(-pi/2) q[93];
rz(pi) q[106];
sx q[106];
rz(2*pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(-pi/2) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
rz(-pi/2) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(pi/2) q[107];
sx q[107];
rz(3*pi/2) q[107];
sx q[107];
rz(5*pi/2) q[107];
rz(1.7915718378090144) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(pi/2) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(-pi/2) q[107];
ecr q[107],q[106];
rz(-pi) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(3*pi/4) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
x q[107];
rz(pi) q[107];
sx q[107];
rz(2*pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(pi/2) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(-pi/2) q[107];
ecr q[107],q[106];
rz(pi) q[106];
sx q[106];
rz(2*pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(-pi/4) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
ecr q[93],q[106];
x q[93];
rz(pi) q[93];
sx q[93];
rz(2*pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(-pi) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(3*pi/2) q[93];
sx q[93];
rz(5*pi/2) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(-pi/2) q[93];
ecr q[93],q[87];
rz(pi/2) q[87];
sx q[87];
rz(pi) q[87];
sx q[87];
rz(3*pi) q[87];
rz(pi/2) q[87];
sx q[87];
rz(3*pi/2) q[87];
sx q[87];
rz(5*pi/2) q[87];
rz(pi/2) q[87];
sx q[87];
rz(3*pi/2) q[87];
sx q[87];
rz(5*pi/2) q[87];
rz(pi/2) q[87];
rz(pi/2) q[87];
sx q[87];
rz(pi/2) q[87];
rz(pi/2) q[87];
x q[93];
rz(pi) q[93];
sx q[93];
rz(2*pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(-pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(3*pi/2) q[93];
sx q[93];
rz(5*pi/2) q[93];
rz(-pi) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(-pi/2) q[93];
ecr q[93],q[87];
rz(-pi/2) q[87];
sx q[87];
rz(pi) q[87];
sx q[87];
rz(3*pi) q[87];
rz(pi/2) q[87];
sx q[87];
rz(3*pi/2) q[87];
sx q[87];
rz(5*pi/2) q[87];
rz(pi/2) q[87];
rz(pi/2) q[87];
sx q[87];
rz(pi/2) q[87];
rz(pi/2) q[87];
x q[93];
rz(pi) q[93];
sx q[93];
rz(2*pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(3*pi/2) q[93];
sx q[93];
rz(5*pi/2) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(-pi/2) q[93];
ecr q[93],q[87];
rz(-pi) q[87];
sx q[87];
rz(pi) q[87];
sx q[87];
rz(3*pi) q[87];
rz(pi/2) q[87];
sx q[87];
rz(3*pi/2) q[87];
sx q[87];
rz(5*pi/2) q[87];
rz(-pi/2) q[87];
sx q[87];
rz(pi) q[87];
sx q[87];
rz(3*pi) q[87];
rz(pi/2) q[87];
sx q[87];
rz(3*pi/2) q[87];
sx q[87];
rz(5*pi/2) q[87];
rz(pi/2) q[87];
rz(pi/2) q[87];
sx q[87];
rz(pi/2) q[87];
rz(pi/2) q[87];
x q[93];
rz(pi) q[93];
sx q[93];
rz(2*pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(3*pi/2) q[93];
sx q[93];
rz(5*pi/2) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(-pi/2) q[93];
rz(pi/2) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
x q[107];
rz(pi) q[107];
sx q[107];
rz(2*pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(2.9208171425756735) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(pi/2) q[107];
sx q[107];
rz(3*pi/2) q[107];
sx q[107];
rz(5*pi/2) q[107];
rz(-pi) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(pi/2) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(-pi/2) q[107];
ecr q[107],q[106];
rz(pi/2) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
x q[107];
rz(pi) q[107];
sx q[107];
rz(2*pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(-pi/2) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(pi/2) q[107];
sx q[107];
rz(3*pi/2) q[107];
sx q[107];
rz(5*pi/2) q[107];
rz(-pi) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(pi/2) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(-pi/2) q[107];
ecr q[107],q[106];
rz(-pi/2) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
x q[107];
rz(pi) q[107];
sx q[107];
rz(2*pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(pi/2) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(pi/2) q[107];
sx q[107];
rz(3*pi/2) q[107];
sx q[107];
rz(5*pi/2) q[107];
rz(pi/2) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(pi/2) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(-pi/2) q[107];
ecr q[107],q[106];
rz(-pi/2) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(-2.462682262665) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(-pi/2) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
ecr q[93],q[106];
x q[93];
rz(pi) q[93];
sx q[93];
rz(2*pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(3*pi/2) q[93];
sx q[93];
rz(5*pi/2) q[93];
rz(-pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(-pi/2) q[93];
ecr q[93],q[87];
rz(-pi) q[87];
sx q[87];
rz(pi) q[87];
sx q[87];
rz(3*pi) q[87];
rz(pi/2) q[87];
sx q[87];
rz(3*pi/2) q[87];
sx q[87];
rz(5*pi/2) q[87];
rz(3*pi/4) q[87];
sx q[87];
rz(pi) q[87];
sx q[87];
rz(3*pi) q[87];
rz(pi/2) q[87];
sx q[87];
rz(3*pi/2) q[87];
sx q[87];
rz(5*pi/2) q[87];
rz(pi/2) q[87];
sx q[87];
rz(3*pi/2) q[87];
sx q[87];
rz(5*pi/2) q[87];
rz(pi/2) q[87];
rz(pi/2) q[87];
sx q[87];
rz(pi/2) q[87];
rz(pi/2) q[87];
x q[93];
rz(pi) q[93];
sx q[93];
rz(2*pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(-pi/2) q[93];
ecr q[93],q[87];
rz(pi/2) q[87];
sx q[87];
rz(pi) q[87];
sx q[87];
rz(3*pi) q[87];
x q[93];
rz(pi) q[93];
sx q[93];
rz(2*pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/4) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(3*pi/2) q[93];
sx q[93];
rz(5*pi/2) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(-pi/2) q[93];
rz(-pi/2) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(2.462682262665) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
x q[107];
rz(pi) q[107];
sx q[107];
rz(2*pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(pi/2) q[107];
sx q[107];
rz(3*pi/2) q[107];
sx q[107];
rz(5*pi/2) q[107];
rz(-pi/2) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(pi/2) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(-pi/2) q[107];
ecr q[107],q[106];
rz(-pi) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(3*pi/4) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
x q[107];
rz(pi) q[107];
sx q[107];
rz(2*pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(pi/2) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(-pi/2) q[107];
ecr q[107],q[106];
rz(-pi) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(-pi/2) q[106];
sx q[106];
rz(pi) q[106];
sx q[106];
rz(3*pi) q[106];
rz(pi/2) q[106];
sx q[106];
rz(3*pi/2) q[106];
sx q[106];
rz(5*pi/2) q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
sx q[106];
rz(pi/2) q[106];
rz(pi/2) q[106];
ecr q[93],q[106];
x q[93];
rz(pi) q[93];
sx q[93];
rz(2*pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
rz(pi/2) q[93];
sx q[93];
rz(3*pi/2) q[93];
sx q[93];
rz(5*pi/2) q[93];
rz(-pi/2) q[93];
sx q[93];
rz(pi) q[93];
sx q[93];
rz(3*pi) q[93];
x q[107];
rz(pi) q[107];
sx q[107];
rz(2*pi) q[107];
sx q[107];
rz(3*pi) q[107];
rz(-pi/4) q[107];
sx q[107];
rz(pi) q[107];
sx q[107];
rz(3*pi) q[107];
measure q[93] -> c[0];
measure q[87] -> c[1];
measure q[107] -> c[2];
measure q[106] -> c[3];