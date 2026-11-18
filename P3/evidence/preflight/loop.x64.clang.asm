
P3/loop/loop.x64.clang:     file format elf64-x86-64


Disassembly of section .init:

Disassembly of section .plt:

Disassembly of section .plt.got:

Disassembly of section .text:

0000000000001190 <main>:
    1190:	55                   	push   %rbp
    1191:	41 57                	push   %r15
    1193:	41 56                	push   %r14
    1195:	41 55                	push   %r13
    1197:	41 54                	push   %r12
    1199:	53                   	push   %rbx
    119a:	48 81 ec 28 30 00 00 	sub    $0x3028,%rsp
    11a1:	c7 44 24 0c 00 00 00 	movl   $0x0,0xc(%rsp)
    11a8:	00 
    11a9:	83 ff 02             	cmp    $0x2,%edi
    11ac:	0f 85 cf 01 00 00    	jne    1381 <main+0x1f1>
    11b2:	48 8b 7e 08          	mov    0x8(%rsi),%rdi
    11b6:	31 f6                	xor    %esi,%esi
    11b8:	ba 0a 00 00 00       	mov    $0xa,%edx
    11bd:	e8 be fe ff ff       	call   1080 <strtol@plt>
    11c2:	48 89 c3             	mov    %rax,%rbx
    11c5:	ff c8                	dec    %eax
    11c7:	83 f8 64             	cmp    $0x64,%eax
    11ca:	0f 83 d0 01 00 00    	jae    13a0 <main+0x210>
    11d0:	48 8d bc 24 20 20 00 	lea    0x2020(%rsp),%rdi
    11d7:	00 
    11d8:	31 ed                	xor    %ebp,%ebp
    11da:	ba 00 10 00 00       	mov    $0x1000,%edx
    11df:	31 f6                	xor    %esi,%esi
    11e1:	e8 8a fe ff ff       	call   1070 <memset@plt>
    11e6:	48 8d bc 24 20 10 00 	lea    0x1020(%rsp),%rdi
    11ed:	00 
    11ee:	ba 00 10 00 00       	mov    $0x1000,%edx
    11f3:	31 f6                	xor    %esi,%esi
    11f5:	e8 76 fe ff ff       	call   1070 <memset@plt>
    11fa:	48 8d 7c 24 20       	lea    0x20(%rsp),%rdi
    11ff:	ba 00 10 00 00       	mov    $0x1000,%edx
    1204:	31 f6                	xor    %esi,%esi
    1206:	e8 65 fe ff ff       	call   1070 <memset@plt>
    120b:	48 8d 74 24 10       	lea    0x10(%rsp),%rsi
    1210:	bf 01 00 00 00       	mov    $0x1,%edi
    1215:	e8 16 fe ff ff       	call   1030 <clock_gettime@plt>
    121a:	85 c0                	test   %eax,%eax
    121c:	0f 85 40 01 00 00    	jne    1362 <main+0x1d2>
    1222:	69 db a0 86 01 00    	imul   $0x186a0,%ebx,%ebx
    1228:	4c 8b 7c 24 10       	mov    0x10(%rsp),%r15
    122d:	4c 8b 74 24 18       	mov    0x18(%rsp),%r14
    1232:	66 66 66 66 66 2e 0f 	data16 data16 data16 data16 cs nopw 0x0(%rax,%rax,1)
    1239:	1f 84 00 00 00 00 00 
    1240:	b8 0c 00 00 00       	mov    $0xc,%eax
    1245:	66 66 2e 0f 1f 84 00 	data16 cs nopw 0x0(%rax,%rax,1)
    124c:	00 00 00 00 
    1250:	66 0f 6f 84 84 f0 0f 	movdqa 0xff0(%rsp,%rax,4),%xmm0
    1257:	00 00 
    1259:	66 0f 6f 8c 84 00 10 	movdqa 0x1000(%rsp,%rax,4),%xmm1
    1260:	00 00 
    1262:	66 0f 6f 94 84 10 10 	movdqa 0x1010(%rsp,%rax,4),%xmm2
    1269:	00 00 
    126b:	66 0f 6f 9c 84 20 10 	movdqa 0x1020(%rsp,%rax,4),%xmm3
    1272:	00 00 
    1274:	66 0f fe 84 84 f0 1f 	paddd  0x1ff0(%rsp,%rax,4),%xmm0
    127b:	00 00 
    127d:	66 0f fe 8c 84 00 20 	paddd  0x2000(%rsp,%rax,4),%xmm1
    1284:	00 00 
    1286:	66 0f 7f 44 84 f0    	movdqa %xmm0,-0x10(%rsp,%rax,4)
    128c:	66 0f 7f 0c 84       	movdqa %xmm1,(%rsp,%rax,4)
    1291:	66 0f fe 94 84 10 20 	paddd  0x2010(%rsp,%rax,4),%xmm2
    1298:	00 00 
    129a:	66 0f fe 9c 84 20 20 	paddd  0x2020(%rsp,%rax,4),%xmm3
    12a1:	00 00 
    12a3:	66 0f 7f 54 84 10    	movdqa %xmm2,0x10(%rsp,%rax,4)
    12a9:	66 0f 7f 5c 84 20    	movdqa %xmm3,0x20(%rsp,%rax,4)
    12af:	48 83 c0 10          	add    $0x10,%rax
    12b3:	48 3d 0c 04 00 00    	cmp    $0x40c,%rax
    12b9:	75 95                	jne    1250 <main+0xc0>
    12bb:	ff c5                	inc    %ebp
    12bd:	39 dd                	cmp    %ebx,%ebp
    12bf:	0f 85 7b ff ff ff    	jne    1240 <main+0xb0>
    12c5:	48 8d 74 24 10       	lea    0x10(%rsp),%rsi
    12ca:	bf 01 00 00 00       	mov    $0x1,%edi
    12cf:	e8 5c fd ff ff       	call   1030 <clock_gettime@plt>
    12d4:	85 c0                	test   %eax,%eax
    12d6:	0f 85 86 00 00 00    	jne    1362 <main+0x1d2>
    12dc:	4c 8b 64 24 10       	mov    0x10(%rsp),%r12
    12e1:	4c 8b 6c 24 18       	mov    0x18(%rsp),%r13
    12e6:	48 8d 7c 24 0c       	lea    0xc(%rsp),%rdi
    12eb:	e8 50 fd ff ff       	call   1040 <rand_r@plt>
    12f0:	8d 88 ff 03 00 00    	lea    0x3ff(%rax),%ecx
    12f6:	85 c0                	test   %eax,%eax
    12f8:	0f 49 c8             	cmovns %eax,%ecx
    12fb:	81 e1 00 fc ff ff    	and    $0xfffffc00,%ecx
    1301:	29 c8                	sub    %ecx,%eax
    1303:	4d 29 fc             	sub    %r15,%r12
    1306:	0f 57 c9             	xorps  %xmm1,%xmm1
    1309:	f2 49 0f 2a cc       	cvtsi2sd %r12,%xmm1
    130e:	48 98                	cltq
    1310:	4d 29 f5             	sub    %r14,%r13
    1313:	0f 57 c0             	xorps  %xmm0,%xmm0
    1316:	f2 49 0f 2a c5       	cvtsi2sd %r13,%xmm0
    131b:	8b 6c 84 20          	mov    0x20(%rsp,%rax,4),%ebp
    131f:	f2 0f 59 05 e1 0c 00 	mulsd  0xce1(%rip),%xmm0        # 2008 <_IO_stdin_used+0x8>
    1326:	00 
    1327:	f2 0f 58 c1          	addsd  %xmm1,%xmm0
    132b:	48 8d 3d 23 0d 00 00 	lea    0xd23(%rip),%rdi        # 2055 <_IO_stdin_used+0x55>
    1332:	48 8d 0d 64 0d 00 00 	lea    0xd64(%rip),%rcx        # 209d <_IO_stdin_used+0x9d>
    1339:	4c 8d 05 5f 0d 00 00 	lea    0xd5f(%rip),%r8        # 209f <_IO_stdin_used+0x9f>
    1340:	be 00 04 00 00       	mov    $0x400,%esi
    1345:	89 da                	mov    %ebx,%edx
    1347:	b0 01                	mov    $0x1,%al
    1349:	e8 02 fd ff ff       	call   1050 <printf@plt>
    134e:	89 e8                	mov    %ebp,%eax
    1350:	48 81 c4 28 30 00 00 	add    $0x3028,%rsp
    1357:	5b                   	pop    %rbx
    1358:	41 5c                	pop    %r12
    135a:	41 5d                	pop    %r13
    135c:	41 5e                	pop    %r14
    135e:	41 5f                	pop    %r15
    1360:	5d                   	pop    %rbp
    1361:	c3                   	ret
    1362:	48 8d 3d 3f 0d 00 00 	lea    0xd3f(%rip),%rdi        # 20a8 <_IO_stdin_used+0xa8>
    1369:	48 8d 35 3f 0d 00 00 	lea    0xd3f(%rip),%rsi        # 20af <_IO_stdin_used+0xaf>
    1370:	48 8d 0d 47 0d 00 00 	lea    0xd47(%rip),%rcx        # 20be <_IO_stdin_used+0xbe>
    1377:	ba 4b 00 00 00       	mov    $0x4b,%edx
    137c:	e8 df fc ff ff       	call   1060 <__assert_fail@plt>
    1381:	48 8d 3d 88 0c 00 00 	lea    0xc88(%rip),%rdi        # 2010 <_IO_stdin_used+0x10>
    1388:	48 8d 35 8b 0c 00 00 	lea    0xc8b(%rip),%rsi        # 201a <_IO_stdin_used+0x1a>
    138f:	48 8d 0d 8b 0c 00 00 	lea    0xc8b(%rip),%rcx        # 2021 <_IO_stdin_used+0x21>
    1396:	ba 3b 00 00 00       	mov    $0x3b,%edx
    139b:	e8 c0 fc ff ff       	call   1060 <__assert_fail@plt>
    13a0:	48 8d 3d 91 0c 00 00 	lea    0xc91(%rip),%rdi        # 2038 <_IO_stdin_used+0x38>
    13a7:	48 8d 35 6c 0c 00 00 	lea    0xc6c(%rip),%rsi        # 201a <_IO_stdin_used+0x1a>
    13ae:	48 8d 0d 6c 0c 00 00 	lea    0xc6c(%rip),%rcx        # 2021 <_IO_stdin_used+0x21>
    13b5:	ba 3d 00 00 00       	mov    $0x3d,%edx
    13ba:	e8 a1 fc ff ff       	call   1060 <__assert_fail@plt>

Disassembly of section .fini:
