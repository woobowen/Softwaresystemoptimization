
P3/loop/loop.x64.gcc:     file format elf64-x86-64


Disassembly of section .init:

Disassembly of section .plt:

Disassembly of section .plt.got:

Disassembly of section .plt.sec:

Disassembly of section .text:

0000000000001100 <main>:
    1100:	f3 0f 1e fa          	endbr64
    1104:	41 57                	push   %r15
    1106:	41 56                	push   %r14
    1108:	41 55                	push   %r13
    110a:	41 54                	push   %r12
    110c:	55                   	push   %rbp
    110d:	53                   	push   %rbx
    110e:	48 81 ec 00 10 00 00 	sub    $0x1000,%rsp
    1115:	48 83 0c 24 00       	orq    $0x0,(%rsp)
    111a:	48 83 ec 28          	sub    $0x28,%rsp
    111e:	64 48 8b 14 25 28 00 	mov    %fs:0x28,%rdx
    1125:	00 00 
    1127:	48 89 94 24 18 10 00 	mov    %rdx,0x1018(%rsp)
    112e:	00 
    112f:	31 d2                	xor    %edx,%edx
    1131:	c7 44 24 0c 00 00 00 	movl   $0x0,0xc(%rsp)
    1138:	00 
    1139:	83 ff 02             	cmp    $0x2,%edi
    113c:	0f 85 14 01 00 00    	jne    1256 <main+0x156>
    1142:	48 8b 7e 08          	mov    0x8(%rsi),%rdi
    1146:	ba 0a 00 00 00       	mov    $0xa,%edx
    114b:	31 f6                	xor    %esi,%esi
    114d:	e8 8e ff ff ff       	call   10e0 <strtol@plt>
    1152:	49 89 c7             	mov    %rax,%r15
    1155:	8d 40 ff             	lea    -0x1(%rax),%eax
    1158:	83 f8 63             	cmp    $0x63,%eax
    115b:	0f 87 19 01 00 00    	ja     127a <main+0x17a>
    1161:	48 8d 5c 24 10       	lea    0x10(%rsp),%rbx
    1166:	31 c0                	xor    %eax,%eax
    1168:	b9 00 02 00 00       	mov    $0x200,%ecx
    116d:	48 89 df             	mov    %rbx,%rdi
    1170:	45 69 ff a0 86 01 00 	imul   $0x186a0,%r15d,%r15d
    1177:	f3 48 ab             	rep stos %rax,%es:(%rdi)
    117a:	e8 11 02 00 00       	call   1390 <gettime>
    117f:	66 0f ef c0          	pxor   %xmm0,%xmm0
    1183:	49 89 d5             	mov    %rdx,%r13
    1186:	49 89 c4             	mov    %rax,%r12
    1189:	31 d2                	xor    %edx,%edx
    118b:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)
    1190:	31 c0                	xor    %eax,%eax
    1192:	66 0f 1f 44 00 00    	nopw   0x0(%rax,%rax,1)
    1198:	0f 29 04 03          	movaps %xmm0,(%rbx,%rax,1)
    119c:	0f 29 44 03 10       	movaps %xmm0,0x10(%rbx,%rax,1)
    11a1:	48 83 c0 20          	add    $0x20,%rax
    11a5:	48 3d 00 10 00 00    	cmp    $0x1000,%rax
    11ab:	75 eb                	jne    1198 <main+0x98>
    11ad:	83 c2 01             	add    $0x1,%edx
    11b0:	44 39 fa             	cmp    %r15d,%edx
    11b3:	7c db                	jl     1190 <main+0x90>
    11b5:	e8 d6 01 00 00       	call   1390 <gettime>
    11ba:	48 8d 7c 24 0c       	lea    0xc(%rsp),%rdi
    11bf:	48 89 d5             	mov    %rdx,%rbp
    11c2:	48 89 c3             	mov    %rax,%rbx
    11c5:	e8 f6 fe ff ff       	call   10c0 <rand_r@plt>
    11ca:	4c 29 ed             	sub    %r13,%rbp
    11cd:	66 0f ef c0          	pxor   %xmm0,%xmm0
    11d1:	4c 29 e3             	sub    %r12,%rbx
    11d4:	f2 48 0f 2a c5       	cvtsi2sd %rbp,%xmm0
    11d9:	66 0f ef c9          	pxor   %xmm1,%xmm1
    11dd:	99                   	cltd
    11de:	44 89 f9             	mov    %r15d,%ecx
    11e1:	f2 0f 59 05 c7 0e 00 	mulsd  0xec7(%rip),%xmm0        # 20b0 <__PRETTY_FUNCTION__.1+0x8>
    11e8:	00 
    11e9:	f2 48 0f 2a cb       	cvtsi2sd %rbx,%xmm1
    11ee:	c1 ea 16             	shr    $0x16,%edx
    11f1:	4c 8d 0d 4e 0e 00 00 	lea    0xe4e(%rip),%r9        # 2046 <_IO_stdin_used+0x46>
    11f8:	01 d0                	add    %edx,%eax
    11fa:	4c 8d 05 4e 0e 00 00 	lea    0xe4e(%rip),%r8        # 204f <_IO_stdin_used+0x4f>
    1201:	bf 02 00 00 00       	mov    $0x2,%edi
    1206:	25 ff 03 00 00       	and    $0x3ff,%eax
    120b:	48 8d 35 46 0e 00 00 	lea    0xe46(%rip),%rsi        # 2058 <_IO_stdin_used+0x58>
    1212:	29 d0                	sub    %edx,%eax
    1214:	ba 00 04 00 00       	mov    $0x400,%edx
    1219:	48 98                	cltq
    121b:	f2 0f 58 c1          	addsd  %xmm1,%xmm0
    121f:	44 8b 74 84 10       	mov    0x10(%rsp,%rax,4),%r14d
    1224:	b8 01 00 00 00       	mov    $0x1,%eax
    1229:	e8 c2 fe ff ff       	call   10f0 <__printf_chk@plt>
    122e:	48 8b 84 24 18 10 00 	mov    0x1018(%rsp),%rax
    1235:	00 
    1236:	64 48 2b 04 25 28 00 	sub    %fs:0x28,%rax
    123d:	00 00 
    123f:	75 34                	jne    1275 <main+0x175>
    1241:	48 81 c4 28 10 00 00 	add    $0x1028,%rsp
    1248:	44 89 f0             	mov    %r14d,%eax
    124b:	5b                   	pop    %rbx
    124c:	5d                   	pop    %rbp
    124d:	41 5c                	pop    %r12
    124f:	41 5d                	pop    %r13
    1251:	41 5e                	pop    %r14
    1253:	41 5f                	pop    %r15
    1255:	c3                   	ret
    1256:	48 8d 0d 4b 0e 00 00 	lea    0xe4b(%rip),%rcx        # 20a8 <__PRETTY_FUNCTION__.1>
    125d:	ba 3b 00 00 00       	mov    $0x3b,%edx
    1262:	48 8d 35 af 0d 00 00 	lea    0xdaf(%rip),%rsi        # 2018 <_IO_stdin_used+0x18>
    1269:	48 8d 3d af 0d 00 00 	lea    0xdaf(%rip),%rdi        # 201f <_IO_stdin_used+0x1f>
    1270:	e8 5b fe ff ff       	call   10d0 <__assert_fail@plt>
    1275:	e8 36 fe ff ff       	call   10b0 <__stack_chk_fail@plt>
    127a:	48 8d 0d 27 0e 00 00 	lea    0xe27(%rip),%rcx        # 20a8 <__PRETTY_FUNCTION__.1>
    1281:	ba 3d 00 00 00       	mov    $0x3d,%edx
    1286:	48 8d 35 8b 0d 00 00 	lea    0xd8b(%rip),%rsi        # 2018 <_IO_stdin_used+0x18>
    128d:	48 8d 3d 95 0d 00 00 	lea    0xd95(%rip),%rdi        # 2029 <_IO_stdin_used+0x29>
    1294:	e8 37 fe ff ff       	call   10d0 <__assert_fail@plt>

Disassembly of section .fini:
