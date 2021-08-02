CC ?= gcc
CFLAGS += -I$(INC_PATH)
LDFLAGS += -shared -fpic
LIBS += -lglut -lGL -lGLU -ldl

MAKEFILE_PATH = $(abspath $(lastword $(MAKEFILE_LIST)))
PROJECT_NAME = $(shell basename $(shell dirname $(MAKEFILE_PATH)))
SRC_PATH = ./src
INC_PATH = ./include

target = lib$(PROJECT_NAME).so
# src = $(wildcard $(SRC_PATH)/*.c)
src = $(SRC_PATH)/glad.c
obj = $(patsubst %.c,%.o,$(src))

ifdef DEBUG
	CFLAGS += -g
endif

all: $(obj)
	@echo -e "\033[1mMaking shared library \033[32m[$(target)]\033[0m"
	@echo obj= $(obj)
	$(CC) $(obj) -o $(target) $(CFLAGS) $(LDFLAGS) $(LIBS)

%.o:%.c
	$(CC) -c $< -o $@ $(CFLAGS) $(LDFLAGS) $(LIBS)

.PHONY: clean
clean:
	rm -rf $(obj) $(target)
