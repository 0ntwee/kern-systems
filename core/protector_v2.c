// code/protector_v2.c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#define KEY 0xAA
#define PAYLOAD_SIZE 32

// Зашифрованный байткод "return 42;"
unsigned char encrypted_payload[PAYLOAD_SIZE] = {
    0xB8 ^ KEY, 0x2A ^ KEY, 0x00 ^ KEY, 0x00 ^ KEY, 0x00 ^ KEY,  // mov eax, 42
    0xC3 ^ KEY, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

typedef int (*func_ptr)();

int main() {
    // 1. Выделить исполняемую память
    void *exec_mem = mmap(NULL, PAYLOAD_SIZE,
                          PROT_READ | PROT_WRITE | PROT_EXEC,
                          MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (exec_mem == MAP_FAILED) {
        perror("mmap");
        exit(1);
    }

    // 2. Расшифровать payload
    for (int i = 0; i < PAYLOAD_SIZE; i++) {
        ((unsigned char*)exec_mem)[i] = encrypted_payload[i] ^ KEY;
    }

    // 3. Вызвать расшифрованный код
    int result = ((func_ptr)exec_mem)();
    printf("[*] Расшифрованный код вернул: %d\n", result);

    munmap(exec_mem, PAYLOAD_SIZE);
    return 0;
}
