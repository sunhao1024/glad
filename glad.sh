git clone https://github.com/Dav1dde/glad.git
cd glad
git checkout c
gcc -fpic src/glad.c -c
gcc -shared -Wl,-z,relro,-z,now -o libglad.so glad.o
sudo cp libglad.so /usr/lib/
sudo cp include/* -r /usr/include
