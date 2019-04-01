// msc-test-app.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include "pch.h"

#include <stdint.h>
#include <windows.h>

extern "C" int __cdecl init(unsigned int output_skip);
extern "C" int __cdecl get_capture_width();
extern "C" int __cdecl get_capture_height();
extern "C" int __cdecl get_bytes_per_pixel();
extern "C" void __cdecl close();
extern "C" const char* __cdecl get_last_error();
extern "C" int __cdecl capture_frame(uint8_t* buffer);

int main()
{
    init(0);

    uint8_t* buffer = new uint8_t[get_capture_width() * get_capture_height() * get_bytes_per_pixel()];

    for (int i = 0; i < 10; ++i) {
        capture_frame(buffer);
        Sleep(2000);
    }

    delete[] buffer;

    close();
}
