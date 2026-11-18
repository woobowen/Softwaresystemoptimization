
P3/loop/loop.aarch64.clang:     file format elf64-littleaarch64


Disassembly of section .init:

Disassembly of section .plt:

Disassembly of section .text:

00000000004007f0 <main>:
  4007f0:	a9bb7bfd 	stp	x29, x30, [sp, #-80]!
  4007f4:	a90167fc 	stp	x28, x25, [sp, #16]
  4007f8:	a9025ff8 	stp	x24, x23, [sp, #32]
  4007fc:	a90357f6 	stp	x22, x21, [sp, #48]
  400800:	a9044ff4 	stp	x20, x19, [sp, #64]
  400804:	910003fd 	mov	x29, sp
  400808:	d1400fff 	sub	sp, sp, #0x3, lsl #12
  40080c:	d10083ff 	sub	sp, sp, #0x20
  400810:	7100081f 	cmp	w0, #0x2
  400814:	b9000fff 	str	wzr, [sp, #12]
  400818:	54000c81 	b.ne	4009a8 <main+0x1b8>  // b.any
  40081c:	f9400420 	ldr	x0, [x1, #8]
  400820:	aa1f03e1 	mov	x1, xzr
  400824:	52800142 	mov	w2, #0xa                   	// #10
  400828:	94001847 	bl	406944 <__strtol>
  40082c:	aa0003f3 	mov	x19, x0
  400830:	51000668 	sub	w8, w19, #0x1
  400834:	7101911f 	cmp	w8, #0x64
  400838:	54000c82 	b.cs	4009c8 <main+0x1d8>  // b.hs, b.nlast
  40083c:	91400be0 	add	x0, sp, #0x2, lsl #12
  400840:	2a1f03e1 	mov	w1, wzr
  400844:	52820002 	mov	w2, #0x1000                	// #4096
  400848:	91004000 	add	x0, x0, #0x10
  40084c:	91400bf4 	add	x20, sp, #0x2, lsl #12
  400850:	91004294 	add	x20, x20, #0x10
  400854:	97fffe9f 	bl	4002d0 <.plt+0x30>
  400858:	914007e0 	add	x0, sp, #0x1, lsl #12
  40085c:	2a1f03e1 	mov	w1, wzr
  400860:	52820002 	mov	w2, #0x1000                	// #4096
  400864:	91004000 	add	x0, x0, #0x10
  400868:	914007f6 	add	x22, sp, #0x1, lsl #12
  40086c:	910042d6 	add	x22, x22, #0x10
  400870:	97fffe98 	bl	4002d0 <.plt+0x30>
  400874:	910043e0 	add	x0, sp, #0x10
  400878:	2a1f03e1 	mov	w1, wzr
  40087c:	52820002 	mov	w2, #0x1000                	// #4096
  400880:	910043f8 	add	x24, sp, #0x10
  400884:	97fffe93 	bl	4002d0 <.plt+0x30>
  400888:	d10043a1 	sub	x1, x29, #0x10
  40088c:	52800020 	mov	w0, #0x1                   	// #1
  400890:	94007360 	bl	41d610 <__clock_gettime>
  400894:	350007a0 	cbnz	w0, 400988 <main+0x198>
  400898:	5290d409 	mov	w9, #0x86a0                	// #34464
  40089c:	d10043b9 	sub	x25, x29, #0x10
  4008a0:	2a1f03e8 	mov	w8, wzr
  4008a4:	72a00029 	movk	w9, #0x1, lsl #16
  4008a8:	a9405737 	ldp	x23, x21, [x25]
  4008ac:	1b097e73 	mul	w19, w19, w9
  4008b0:	52820209 	mov	w9, #0x1010                	// #4112
  4008b4:	5280020a 	mov	w10, #0x10                  	// #16
  4008b8:	8b0a028b 	add	x11, x20, x10
  4008bc:	8b0a02cc 	add	x12, x22, x10
  4008c0:	ad7f8d80 	ldp	q0, q3, [x12, #-16]
  4008c4:	ad7f8961 	ldp	q1, q2, [x11, #-16]
  4008c8:	8b0a030b 	add	x11, x24, x10
  4008cc:	9100814a 	add	x10, x10, #0x20
  4008d0:	eb09015f 	cmp	x10, x9
  4008d4:	4ea18400 	add	v0.4s, v0.4s, v1.4s
  4008d8:	4ea28461 	add	v1.4s, v3.4s, v2.4s
  4008dc:	ad3f8560 	stp	q0, q1, [x11, #-16]
  4008e0:	54fffec1 	b.ne	4008b8 <main+0xc8>  // b.any
  4008e4:	11000508 	add	w8, w8, #0x1
  4008e8:	6b13011f 	cmp	w8, w19
  4008ec:	54fffe41 	b.ne	4008b4 <main+0xc4>  // b.any
  4008f0:	d10043a1 	sub	x1, x29, #0x10
  4008f4:	52800020 	mov	w0, #0x1                   	// #1
  4008f8:	94007346 	bl	41d610 <__clock_gettime>
  4008fc:	35000460 	cbnz	w0, 400988 <main+0x198>
  400900:	a9405b34 	ldp	x20, x22, [x25]
  400904:	910033e0 	add	x0, sp, #0xc
  400908:	940017f2 	bl	4068d0 <rand_r>
  40090c:	cb170288 	sub	x8, x20, x23
  400910:	cb1502c9 	sub	x9, x22, x21
  400914:	900002c3 	adrp	x3, 458000 <_Unwind_Find_FDE+0x4e0>
  400918:	91311463 	add	x3, x3, #0xc45
  40091c:	9e620100 	scvtf	d0, x8
  400920:	9e620121 	scvtf	d1, x9
  400924:	900002c8 	adrp	x8, 458000 <_Unwind_Find_FDE+0x4e0>
  400928:	12002409 	and	w9, w0, #0x3ff
  40092c:	900002c4 	adrp	x4, 458000 <_Unwind_Find_FDE+0x4e0>
  400930:	91311c84 	add	x4, x4, #0xc47
  400934:	fd45bd02 	ldr	d2, [x8, #2936]
  400938:	6b0003e8 	negs	w8, w0
  40093c:	12002508 	and	w8, w8, #0x3ff
  400940:	900002c0 	adrp	x0, 458000 <_Unwind_Find_FDE+0x4e0>
  400944:	912ff400 	add	x0, x0, #0xbfd
  400948:	1f420020 	fmadd	d0, d1, d2, d0
  40094c:	5a884528 	csneg	w8, w9, w8, mi	// mi = first
  400950:	910043e9 	add	x9, sp, #0x10
  400954:	b868d934 	ldr	w20, [x9, w8, sxtw #2]
  400958:	52808001 	mov	w1, #0x400                 	// #1024
  40095c:	2a1303e2 	mov	w2, w19
  400960:	94001b54 	bl	4076b0 <_IO_printf>
  400964:	2a1403e0 	mov	w0, w20
  400968:	91400fff 	add	sp, sp, #0x3, lsl #12
  40096c:	910083ff 	add	sp, sp, #0x20
  400970:	a9444ff4 	ldp	x20, x19, [sp, #64]
  400974:	a94357f6 	ldp	x22, x21, [sp, #48]
  400978:	a9425ff8 	ldp	x24, x23, [sp, #32]
  40097c:	a94167fc 	ldp	x28, x25, [sp, #16]
  400980:	a8c57bfd 	ldp	x29, x30, [sp], #80
  400984:	d65f03c0 	ret
  400988:	900002c0 	adrp	x0, 458000 <_Unwind_Find_FDE+0x4e0>
  40098c:	91314000 	add	x0, x0, #0xc50
  400990:	900002c1 	adrp	x1, 458000 <_Unwind_Find_FDE+0x4e0>
  400994:	91315c21 	add	x1, x1, #0xc57
  400998:	900002c3 	adrp	x3, 458000 <_Unwind_Find_FDE+0x4e0>
  40099c:	91319863 	add	x3, x3, #0xc66
  4009a0:	52800962 	mov	w2, #0x4b                  	// #75
  4009a4:	9400026b 	bl	401350 <__assert_fail>
  4009a8:	900002c0 	adrp	x0, 458000 <_Unwind_Find_FDE+0x4e0>
  4009ac:	912ee000 	add	x0, x0, #0xbb8
  4009b0:	900002c1 	adrp	x1, 458000 <_Unwind_Find_FDE+0x4e0>
  4009b4:	912f0821 	add	x1, x1, #0xbc2
  4009b8:	900002c3 	adrp	x3, 458000 <_Unwind_Find_FDE+0x4e0>
  4009bc:	912f2463 	add	x3, x3, #0xbc9
  4009c0:	52800762 	mov	w2, #0x3b                  	// #59
  4009c4:	94000263 	bl	401350 <__assert_fail>
  4009c8:	900002c0 	adrp	x0, 458000 <_Unwind_Find_FDE+0x4e0>
  4009cc:	912f8000 	add	x0, x0, #0xbe0
  4009d0:	900002c1 	adrp	x1, 458000 <_Unwind_Find_FDE+0x4e0>
  4009d4:	912f0821 	add	x1, x1, #0xbc2
  4009d8:	900002c3 	adrp	x3, 458000 <_Unwind_Find_FDE+0x4e0>
  4009dc:	912f2463 	add	x3, x3, #0xbc9
  4009e0:	528007a2 	mov	w2, #0x3d                  	// #61
  4009e4:	9400025b 	bl	401350 <__assert_fail>

Disassembly of section .fini:
