// code/protector_v1.c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int is_debugged() {
    FILE *f = fopen("/proc/self/status", "r");
    if (!f) return 0;

    char line[256];
    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line, "TracerPid:", 10) == 0) {
            int tracer_pid = atoi(line + 10);
            fclose(f);
            return tracer_pid != 0;
        }
    }
    fclose(f);
    return 0;
}

int secret_algorithm() {
    return 42;
}

int main() {
    if (is_debugged()) {
        fprintf(stderr, "[!] Отладка обнаружена через TracerPid. Завершение.\n");
        exit(1);
    }

    printf("[+] Защита пройдена. Выполнение защищённого кода...\n");
    printf("[*] Результат: %d\n", secret_algorithm());
    return 0;
}
