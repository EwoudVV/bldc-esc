#include <stddef.h>
#include <stdint.h>
void *memset(void *dst, int value, size_t size) {
    unsigned char *d = dst;
    while (size--) *d++ = (unsigned char)value;
    return dst;
}
void *memcpy(void *dst, const void *src, size_t size) {
    unsigned char *d = dst; const unsigned char *s = src;
    while (size--) *d++ = *s++;
    return dst;
}
void *memmove(void *dst, const void *src, size_t size) {
    unsigned char *d = dst; const unsigned char *s = src;
    if ((uintptr_t)d < (uintptr_t)s) { while (size--) *d++ = *s++; }
    else { d += size; s += size; while (size--) *--d = *--s; }
    return dst;
}
