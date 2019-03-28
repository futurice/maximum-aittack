# dxgi-screen-capture

Screen capturing for Markku based on Windows DXGI 1.2 Desktop Duplication API. Works on all Windows starting from Windows 8 and should be able to capture all kinds of applications,  whether they are windowed, full-screen, Direct3D or OpenGL.

## Introduction

A Visual Studio 2017 solution is included that can be used to compile a DLL that exports a C API to perform screen captures. Main use case is to call this API through python FFI, but it should work with pretty much any other language. The solution also includes a very simple C++ application that can be used to do e.g. debugging.

## Usage

Current screen is captured to a memory buffer reserved by the user of the API. The usage roughly goes as follows:
- call `init()` before any other methods to initialize screen capturing
- call `get_capture_width()`, `get_capture_height()` and `get_bytes_per_pixel()` to find out how big of a memory buffer you need to store the screen
- call `capture_frame()` whenever you want to capture the current screen
- call `close()` when you are finished doing screen captures

All methods will return a negative integer on error and 0 on success. The error is usually a DXGI error code, or -1 in case of general errors such as attempting to do stuff before calling `init()`. You can use `get_last_error()` to get a human-readable description of the last error occurred.

## Known caveats and issues

- First frame captured is usually just an empty, black screen. This seems to be just how Desktop Duplication API works as it tracks changes in dirty regions and pointer positions, so the first capture is always a void, initial state
- If you ask for screen captures very frequently and there has not been any changes since the last frame, `capture_frame()` will return `0x887A0027 (DXGI_ERROR_WAIT_TIMEOUT)` to indicate this. You can presume that the contents of the current frame exactly match the last frame you captured. `capture_frame()` will internally wait up to 10ms for changes
- All display adapters are iterated for suitable outputs and the first adapter/output combo that is attached to the desktop and supports display duplication is selected. There is no adapter/output enumeration method that one could call before `init()` (that'd require some work as APIs other than DXGI would need to be used to discover e.g. names of the adapters). There is only the `output_skip` parameter for `init()` that can be used in scenarios where there's a adapter with multiple suitable outputs (multi-monitor configuration) and the wrong monitor gets selected. Setting this parameter 1, 2, ... instead of 0 allows picking outputs/monitor other than the primary
- Capturing from multiple monitors simultaneously is currently not supported
- If there is changes to configuration after init(), e.g. screen resolution is changed, `capture_frame()` will return `0x887A0026 (DXGI_ERROR_ACCESS_LOST)` to indicate this. You should restart the screen capturing by calling `close()` and `init()`

## Related materials and links

- DXGI MSDN documentation: https://docs.microsoft.com/en-us/windows/desktop/direct3ddxgi/dx-graphics-dxgi, notice especially error code documentation: https://docs.microsoft.com/en-us/windows/desktop/direct3ddxgi/dxgi-error
- Blog post about creating a DLL with desktop duplication and using it through Python FFI: https://medium.com/steveindusteves/playing-games-with-python-9be869f7b189
- MSDN dektop duplication sample: https://code.msdn.microsoft.com/windowsdesktop/Desktop-Duplication-Sample-da4c696a and a related article explaining a more simple approach than taken in the sample: https://www.codeproject.com/Tips/1116253/Desktop-Screen-Capture-on-Windows-via-Windows-Desk
