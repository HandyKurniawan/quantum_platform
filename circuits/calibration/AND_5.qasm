OPENQASM 2.0;
include "qelib1.inc";
qreg q[5];
creg c[5];
x q[0];
x q[1];
x q[2];
x q[3];
u3(0,0,-pi/4) q[3];
u3(pi/2,0,pi) q[4];
cx q[3],q[4];
u3(0,0,pi/4) q[4];
cx q[3],q[4];
u3(0,0,-pi/4) q[4];
u3(pi/2,0,pi) q[4];
u3(pi/2,0,pi) q[4];
u3(pi/2,0,pi) q[3];
u3(0,0,pi/4) q[3];
cx q[2],q[3];
u3(0,0,-pi/4) q[3];
u3(pi/2,0,pi) q[3];
cx q[0],q[3];
u3(0,0,pi/4) q[3];
cx q[1],q[3];
u3(0,0,-pi/4) q[3];
cx q[0],q[3];
u3(0,0,pi/4) q[3];
cx q[1],q[3];
u3(0,0,-pi/4) q[3];
u3(pi/2,0,pi) q[3];
u3(0,0,pi/4) q[3];
cx q[2],q[3];
u3(0,0,-pi/4) q[3];
u3(pi/2,0,pi) q[3];
u3(0,0,pi/4) q[3];
cx q[3],q[4];
u3(0,0,-pi/4) q[4];
cx q[3],q[4];
u3(0,0,pi/4) q[4];
u3(pi/2,0,pi) q[4];
u2(0,pi) q[4];
u3(pi/2,-2*pi,pi) q[3];
u3(0,0,pi/4) q[3];
cx q[2],q[3];
u3(0,0,-pi/4) q[3];
u3(pi/2,-2*pi,pi) q[3];
u3(0,0,pi/4) q[3];
cx q[1],q[3];
u3(0,0,-pi/4) q[3];
cx q[0],q[3];
u3(0,0,pi/4) q[3];
cx q[1],q[3];
u3(0,0,-pi/4) q[3];
cx q[0],q[3];
u1(-pi/16) q[0];
cx q[0],q[4];
u1(pi/16) q[4];
cx q[0],q[4];
u1(-pi/16) q[4];
u2(0,pi) q[4];
u2(0,pi) q[4];
cx q[0],q[1];
u1(pi/16) q[1];
cx q[1],q[4];
u1(-pi/16) q[4];
cx q[1],q[4];
u1(pi/16) q[4];
u2(0,pi) q[4];
u2(0,pi) q[4];
cx q[0],q[1];
u1(-pi/16) q[1];
cx q[1],q[4];
u1(pi/16) q[4];
cx q[1],q[4];
u1(-pi/16) q[4];
u2(0,pi) q[4];
u2(0,pi) q[4];
u3(pi/2,-2*pi,pi) q[3];
u3(0,0,pi/4) q[3];
cx q[2],q[3];
cx q[1],q[2];
u1(pi/16) q[2];
cx q[2],q[4];
u1(-pi/16) q[4];
cx q[2],q[4];
u1(pi/16) q[4];
u2(0,pi) q[4];
u2(0,pi) q[4];
cx q[0],q[2];
u1(-pi/16) q[2];
cx q[2],q[4];
u1(pi/16) q[4];
cx q[2],q[4];
u1(-pi/16) q[4];
u2(0,pi) q[4];
u2(0,pi) q[4];
cx q[1],q[2];
u1(pi/16) q[2];
cx q[2],q[4];
u1(-pi/16) q[4];
cx q[2],q[4];
u1(pi/16) q[4];
u2(0,pi) q[4];
u2(0,pi) q[4];
cx q[0],q[2];
u1(-pi/16) q[2];
cx q[2],q[4];
u1(pi/16) q[4];
cx q[2],q[4];
u1(-pi/16) q[4];
u2(0,pi) q[4];
u3(0,0,-pi/4) q[3];
u3(pi/2,-2*pi,pi) q[3];
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
measure q[3] -> c[3];
measure q[4] -> c[4];