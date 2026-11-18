
P3/loop/loop.aarch64.gcc:     file format elf64-littleaarch64


Disassembly of section .init:

Disassembly of section .plt:

Disassembly of section .text:

0000000000400600 <main>:
  400600:	a9bc7bfd 	stp	x29, x30, [sp, #-64]!
  400604:	d286040d 	mov	x13, #0x3020                	// #12320
  400608:	910003fd 	mov	x29, sp
  40060c:	a90153f3 	stp	x19, x20, [sp, #16]
  400610:	a9025bf5 	stp	x21, x22, [sp, #32]
  400614:	a90363f7 	stp	x23, x24, [sp, #48]
  400618:	cb2d63ff 	sub	sp, sp, x13
  40061c:	f90203ff 	str	xzr, [sp, #1024]
  400620:	f00004e2 	adrp	x2, 49f000 <tunable_list+0x890>
  400624:	f9462442 	ldr	x2, [x2, #3144]
  400628:	f9400043 	ldr	x3, [x2]
  40062c:	f9180fe3 	str	x3, [sp, #12312]
  400630:	d2800003 	mov	x3, #0x0                   	// #0
  400634:	b9000fff 	str	wzr, [sp, #12]
  400638:	7100081f 	cmp	w0, #0x2
  40063c:	54000b41 	b.ne	4007a4 <main+0x1a4>  // b.any
  400640:	f9400420 	ldr	x0, [x1, #8]
  400644:	52800142 	mov	w2, #0xa                   	// #10
  400648:	d2800001 	mov	x1, #0x0                   	// #0
  40064c:	940018de 	bl	4069c4 <__strtol>
  400650:	aa0003f6 	mov	x22, x0
  400654:	51000400 	sub	w0, w0, #0x1
  400658:	71018c1f 	cmp	w0, #0x63
  40065c:	54000b88 	b.hi	4007cc <main+0x1cc>  // b.pmore
  400660:	910043f5 	add	x21, sp, #0x10
  400664:	d2820002 	mov	x2, #0x1000                	// #4096
  400668:	52800001 	mov	w1, #0x0                   	// #0
  40066c:	aa1503e0 	mov	x0, x21
  400670:	97ffff0c 	bl	4002a0 <.plt+0x30>
  400674:	d2820200 	mov	x0, #0x1010                	// #4112
  400678:	8b2063f4 	add	x20, sp, x0
  40067c:	d2820002 	mov	x2, #0x1000                	// #4096
  400680:	52800001 	mov	w1, #0x0                   	// #0
  400684:	aa1403e0 	mov	x0, x20
  400688:	97ffff06 	bl	4002a0 <.plt+0x30>
  40068c:	d2840201 	mov	x1, #0x2010                	// #8208
  400690:	d2820002 	mov	x2, #0x1000                	// #4096
  400694:	8b2163f3 	add	x19, sp, x1
  400698:	52800001 	mov	w1, #0x0                   	// #0
  40069c:	aa1303e0 	mov	x0, x19
  4006a0:	97ffff00 	bl	4002a0 <.plt+0x30>
  4006a4:	940000c3 	bl	4009b0 <gettime>
  4006a8:	aa0103f8 	mov	x24, x1
  4006ac:	5290d403 	mov	w3, #0x86a0                	// #34464
  4006b0:	d2860202 	mov	x2, #0x3010                	// #12304
  4006b4:	72a00023 	movk	w3, #0x1, lsl #16
  4006b8:	aa0003f7 	mov	x23, x0
  4006bc:	8b2263e4 	add	x4, sp, x2
  4006c0:	52800005 	mov	w5, #0x0                   	// #0
  4006c4:	1b167c76 	mul	w22, w3, w22
  4006c8:	aa1303e0 	mov	x0, x19
  4006cc:	aa1403e2 	mov	x2, x20
  4006d0:	aa1503e1 	mov	x1, x21
  4006d4:	d503201f 	nop
  4006d8:	3cc10440 	ldr	q0, [x2], #16
  4006dc:	3cc10421 	ldr	q1, [x1], #16
  4006e0:	4ea18400 	add	v0.4s, v0.4s, v1.4s
  4006e4:	3c810400 	str	q0, [x0], #16
  4006e8:	eb04001f 	cmp	x0, x4
  4006ec:	54ffff61 	b.ne	4006d8 <main+0xd8>  // b.any
  4006f0:	110004a5 	add	w5, w5, #0x1
  4006f4:	6b1600bf 	cmp	w5, w22
  4006f8:	54fffe8b 	b.lt	4006c8 <main+0xc8>  // b.tstop
  4006fc:	940000ad 	bl	4009b0 <gettime>
  400700:	aa0103f5 	mov	x21, x1
  400704:	aa0003f4 	mov	x20, x0
  400708:	cb1802b5 	sub	x21, x21, x24
  40070c:	910033e0 	add	x0, sp, #0xc
  400710:	94001890 	bl	406950 <rand_r>
  400714:	90000301 	adrp	x1, 460000 <__PRETTY_FUNCTION__.0+0x60>
  400718:	9e6202a0 	scvtf	d0, x21
  40071c:	cb170294 	sub	x20, x20, x23
  400720:	52808002 	mov	w2, #0x400                 	// #1024
  400724:	fd420c22 	ldr	d2, [x1, #1048]
  400728:	6b0003e1 	negs	w1, w0
  40072c:	9e620281 	scvtf	d1, x20
  400730:	12002421 	and	w1, w1, #0x3ff
  400734:	12002400 	and	w0, w0, #0x3ff
  400738:	2a1603e3 	mov	w3, w22
  40073c:	1f420400 	fmadd	d0, d0, d2, d1
  400740:	5a814400 	csneg	w0, w0, w1, mi	// mi = first
  400744:	b00002c5 	adrp	x5, 459000 <_Unwind_Find_FDE+0x4d0>
  400748:	b00002c4 	adrp	x4, 459000 <_Unwind_Find_FDE+0x4d0>
  40074c:	912f60a5 	add	x5, x5, #0xbd8
  400750:	912fa084 	add	x4, x4, #0xbe8
  400754:	b860da73 	ldr	w19, [x19, w0, sxtw #2]
  400758:	b00002c1 	adrp	x1, 459000 <_Unwind_Find_FDE+0x4d0>
  40075c:	52800040 	mov	w0, #0x2                   	// #2
  400760:	912fc021 	add	x1, x1, #0xbf0
  400764:	94006d77 	bl	41bd40 <___printf_chk>
  400768:	f00004e0 	adrp	x0, 49f000 <tunable_list+0x890>
  40076c:	f9462400 	ldr	x0, [x0, #3144]
  400770:	f9580fe2 	ldr	x2, [sp, #12312]
  400774:	f9400001 	ldr	x1, [x0]
  400778:	eb010042 	subs	x2, x2, x1
  40077c:	d2800001 	mov	x1, #0x0                   	// #0
  400780:	54000241 	b.ne	4007c8 <main+0x1c8>  // b.any
  400784:	d286040d 	mov	x13, #0x3020                	// #12320
  400788:	8b2d63ff 	add	sp, sp, x13
  40078c:	2a1303e0 	mov	w0, w19
  400790:	a94153f3 	ldp	x19, x20, [sp, #16]
  400794:	a9425bf5 	ldp	x21, x22, [sp, #32]
  400798:	a94363f7 	ldp	x23, x24, [sp, #48]
  40079c:	a8c47bfd 	ldp	x29, x30, [sp], #64
  4007a0:	d65f03c0 	ret
  4007a4:	90000303 	adrp	x3, 460000 <__PRETTY_FUNCTION__.0+0x60>
  4007a8:	91116063 	add	x3, x3, #0x458
  4007ac:	b00002c1 	adrp	x1, 459000 <_Unwind_Find_FDE+0x4d0>
  4007b0:	b00002c0 	adrp	x0, 459000 <_Unwind_Find_FDE+0x4d0>
  4007b4:	91002063 	add	x3, x3, #0x8
  4007b8:	912e8021 	add	x1, x1, #0xba0
  4007bc:	912ea000 	add	x0, x0, #0xba8
  4007c0:	52800762 	mov	w2, #0x3b                  	// #59
  4007c4:	940002f7 	bl	4013a0 <__assert_fail>
  4007c8:	94006d92 	bl	41be10 <__stack_chk_fail>
  4007cc:	90000303 	adrp	x3, 460000 <__PRETTY_FUNCTION__.0+0x60>
  4007d0:	91116063 	add	x3, x3, #0x458
  4007d4:	b00002c1 	adrp	x1, 459000 <_Unwind_Find_FDE+0x4d0>
  4007d8:	b00002c0 	adrp	x0, 459000 <_Unwind_Find_FDE+0x4d0>
  4007dc:	91002063 	add	x3, x3, #0x8
  4007e0:	912e8021 	add	x1, x1, #0xba0
  4007e4:	912ee000 	add	x0, x0, #0xbb8
  4007e8:	528007a2 	mov	w2, #0x3d                  	// #61
  4007ec:	940002ed 	bl	4013a0 <__assert_fail>

Disassembly of section .fini:
