CC = gcc
CFLAGS += -fpic -Iinclude
LDFLAGS += -shared

target = libglad.so
src = $(wildcard ./src/glad.c)
obj = $(patsubst %.c,%.o,$(src))
$(info src=$(src))

all: $(obj)
	$(CC) $(obj) -o $(target) $(CFLAGS) $(LDFLAGS)

%.o:%.c
	$(CC) -c $< -o $@ $(CFLAGS)

.PHONY: clean
clean:
	rm -rf $(obj) $(target)

# gcc -fpic src/glad.c -c -Iinclude
# gcc -shared -Wl,-z,relro,-z,now -o libglad.so glad.o
