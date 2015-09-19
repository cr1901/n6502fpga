test_prog.bin: test_prog.obj 
	wlalink -bi linkfile.txt test_prog.bin

test_prog.obj: test_prog.asm
	wla-6502 -oq test_prog.asm test_prog.obj

upload: test_prog.bin
	python3 loadprog.py -v --port 22 test_prog.bin

dump: test_prog.bin
	python3 ymdump.py --port 22

clean:
	rm -rf test_prog.obj test_prog.bin
