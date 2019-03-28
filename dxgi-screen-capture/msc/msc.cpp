// msc.cpp: screen capturing for Markku based on Windows DXGI 1.2 Desktop Duplication API

#include "targetver.h"

#define WIN32_LEAN_AND_MEAN             // Exclude rarely-used stuff from Windows headers
// Windows Header Files
#include <windows.h>

#include <iostream>
#include <sstream>
#include <vector>

#include <dxgi1_2.h>
#include <d3d11.h>

struct CaptureContext {
    IDXGIFactory1* dxgiFactory;

    IDXGIAdapter1* dxgiAdapter;
    IDXGIOutput1* dxgiOutput;

    ID3D11Device* d3dDevice;
    ID3D11DeviceContext* d3dDeviceContext;

    IDXGIOutputDuplication* dxgiOutputDuplication;
    DXGI_OUTDUPL_DESC dxgiOutputDuplicationDesc;

    std::string lastError;

    CaptureContext() : dxgiFactory(nullptr), dxgiAdapter(nullptr), dxgiOutput(nullptr),
        d3dDevice(nullptr), d3dDeviceContext(nullptr),
        dxgiOutputDuplication(nullptr) {
    }
};

static CaptureContext captureContext;

HRESULT enumerateAdapters(IDXGIFactory1* dxgiFactory, std::vector<IDXGIAdapter1*>& dxgiAdapters);
HRESULT enumerateOutputs(IDXGIAdapter1* dxgiAdapter, std::vector<IDXGIOutput1*>& dxgiOutputs);
HRESULT activateOutputDuplication(IDXGIAdapter1* dxgiAdapter, IDXGIOutput1* dxgiOutput,
    ID3D11Device** d3dDevice, ID3D11DeviceContext** d3dDeviceContext,
    IDXGIOutputDuplication** dxgiOutputDuplication, DXGI_OUTDUPL_DESC *outputDuplicationDesc);

void releaseAllAdapters(std::vector<IDXGIAdapter1*>& dxgiAdapters);
void releaseAllOutputs(std::vector<IDXGIOutput1*>& dxgiOutputs);

// Initialize DXGI Desktop Duplication by selecting a suitable adapter and output (monitor). Should usually be called
// with 'output_skip' set to 0, but if you have multi-monitor setup where you want to capture contents of non-primary
// monitor, use value of 1, 2, ... to skip outputs. Returns Windows HRESULT signifying the result, which would be
// 0 / S_OK for success and negative for error (usually matching some DXGI error)
extern "C" __declspec(dllexport) int init(unsigned int output_skip) {
    HRESULT dxgiFactoryResult = CreateDXGIFactory1(__uuidof(IDXGIFactory1), (void**)&captureContext.dxgiFactory);
    if (FAILED(dxgiFactoryResult)) {
        std::stringstream error;
        error << "CreateDXGIFactory1() failed with 0x" << std::hex << dxgiFactoryResult;
        captureContext.lastError = error.str();
        return dxgiFactoryResult;
    }

    std::vector<IDXGIAdapter1*> adapters;
    enumerateAdapters(captureContext.dxgiFactory, adapters);
    std::cout << "msc: found total of " << adapters.size() << " adapters" << std::endl;

    IDXGIAdapter1* selectedAdapter = nullptr;
    IDXGIOutput1* selectedOutput = nullptr;
    ID3D11Device* d3dDevice = nullptr;
    ID3D11DeviceContext* d3dDeviceContext = nullptr;
    IDXGIOutputDuplication* dxgiOutputDuplication = nullptr;
    DXGI_OUTDUPL_DESC dxgiOutputDuplicationDesc;

    for (size_t a = 0; a < adapters.size() && selectedAdapter == nullptr; ++a) {
        IDXGIAdapter1* adapter = adapters[a];
        std::vector<IDXGIOutput1*> outputs;
        enumerateOutputs(adapters[a], outputs);

        std::cout << "msc: found " << outputs.size() << " suitable output(s) for adapter " << a << std::endl;

        for (size_t b = output_skip; b < outputs.size() && selectedAdapter == nullptr; ++b) {
            IDXGIOutput1* output = outputs[b];
            HRESULT activationResult = activateOutputDuplication(adapter, output, &d3dDevice, &d3dDeviceContext, &dxgiOutputDuplication, &dxgiOutputDuplicationDesc);

            if (SUCCEEDED(activationResult)) {
                selectedAdapter = adapter;
                selectedAdapter->AddRef();
                selectedOutput = output;
                selectedOutput->AddRef();

                std::cout << "msc: selected output " << b << " of adapter " << a << " for duplication" << std::endl;
            }
            else {
                std::cout << "msc: ignoring output " << b << " of adapter " << a << " due to output duplication activation error 0x" << std::hex << activationResult << std::endl;
            }
        }

        releaseAllOutputs(outputs);
    }

    releaseAllAdapters(adapters);

    if (selectedAdapter == nullptr) {
        std::stringstream error;
        error << "Could not find suitable adapter/output";
        captureContext.lastError = error.str();
        return -1;
    }
    captureContext.dxgiAdapter = selectedAdapter;
    captureContext.dxgiOutput = selectedOutput;

    captureContext.d3dDevice = d3dDevice;
    captureContext.d3dDeviceContext = d3dDeviceContext;

    captureContext.dxgiOutputDuplication = dxgiOutputDuplication;
    captureContext.dxgiOutputDuplicationDesc = dxgiOutputDuplicationDesc;

    return S_OK;
}

extern "C" __declspec(dllexport) int get_capture_width() {
    if (captureContext.dxgiOutputDuplication == nullptr) {
        return -1;
    }

    return captureContext.dxgiOutputDuplicationDesc.ModeDesc.Width;
}

extern "C" __declspec(dllexport) int get_capture_height() {
    if (captureContext.dxgiOutputDuplication == nullptr) {
        return -1;
    }

    return captureContext.dxgiOutputDuplicationDesc.ModeDesc.Height;
}

extern "C" __declspec(dllexport) int get_bytes_per_pixel() {
    if (captureContext.dxgiOutputDuplication == nullptr) {
        return -1;
    }

    // @todo: currently assumes 32-bit pixel format, could parse this from output duplication desc's format
    return 4;
}

extern "C" __declspec(dllexport) void close() {
    if (captureContext.dxgiOutputDuplication != nullptr) {
        captureContext.dxgiOutputDuplication->Release();
        captureContext.dxgiOutputDuplication = nullptr;
    }

    if (captureContext.d3dDeviceContext != nullptr) {
        captureContext.d3dDeviceContext->Release();
        captureContext.d3dDeviceContext = nullptr;
    }

    if (captureContext.d3dDevice != nullptr) {
        captureContext.d3dDevice->Release();
        captureContext.d3dDevice = nullptr;
    }

    if (captureContext.dxgiOutput != nullptr) {
        captureContext.dxgiOutput->Release();
        captureContext.dxgiOutput = nullptr;
    }

    if (captureContext.dxgiAdapter != nullptr) {
        captureContext.dxgiAdapter->Release();
        captureContext.dxgiAdapter = nullptr;
    }

    if (captureContext.dxgiFactory != nullptr) {
        captureContext.dxgiFactory->Release();
        captureContext.dxgiFactory = nullptr;
    }
}

extern "C" __declspec(dllexport) const char* get_last_error() {
    return captureContext.lastError.c_str();
}

extern "C" __declspec(dllexport) int capture_frame(uint8_t* buffer) {
    if (captureContext.dxgiOutputDuplication == nullptr) {
        return -1;
    }

    // @todo: code here will leak handles if there's errors in staging texture creation or in memory mapping operations.
    // These really should not happen unless out of memory. Most common error scenario will hapen with AcquireNextFrame(),
    // in this case no handles should be leaked.
    // @todo: code here presumes that screen buffer is always in GPU memory and it needs to be copied to a staging buffer.
    // DXGI_OUTDUPL_DESC::DesktopImageInSystemMemory could be used to detect if the screen buffer is already in system
    // memory and could be directly mapped with IDXGIOutputDuplication::MapDesktopSurface(). But no hardware was available
    // to test this at the time of writing this, assumption is that this would work with integrated GPUs.
    DXGI_OUTDUPL_FRAME_INFO captureFrameInfo;
    IDXGIResource* dxgiResource = nullptr;

    HRESULT frameCaptureResult = captureContext.dxgiOutputDuplication->AcquireNextFrame(10, &captureFrameInfo, &dxgiResource);
    if (FAILED(frameCaptureResult)) {
        std::stringstream error;
        error << "IDXGIOutputDuplication::AcquireNextFrame() failed with  0x" << std::hex << frameCaptureResult;
        captureContext.lastError = error.str();
        return frameCaptureResult;
    }

    ID3D11Texture2D* captureTexture = nullptr;
    HRESULT captureTextureQiResult = dxgiResource->QueryInterface(__uuidof(ID3D11Texture2D), (void**)&captureTexture);
    dxgiResource->Release();

    if (FAILED(captureTextureQiResult)) {
        std::stringstream error;
        error << "Capture texture QueryInterface() failed with  0x" << std::hex << captureTextureQiResult;
        captureContext.lastError = error.str();
        return captureTextureQiResult;
    }

    D3D11_TEXTURE2D_DESC stagingTextureDesc;
    stagingTextureDesc.Width = captureContext.dxgiOutputDuplicationDesc.ModeDesc.Width;
    stagingTextureDesc.Height = captureContext.dxgiOutputDuplicationDesc.ModeDesc.Height;
    stagingTextureDesc.Format = captureContext.dxgiOutputDuplicationDesc.ModeDesc.Format;
    stagingTextureDesc.MipLevels = 1;
    stagingTextureDesc.ArraySize = 1;
    stagingTextureDesc.SampleDesc.Count = 1;
    stagingTextureDesc.SampleDesc.Quality = 0;
    stagingTextureDesc.Usage = D3D11_USAGE_STAGING;
    stagingTextureDesc.BindFlags = 0;
    stagingTextureDesc.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
    stagingTextureDesc.MiscFlags = 0;

    ID3D11Texture2D* stagingTexture = nullptr;
    HRESULT stagingTextureCreateResult = captureContext.d3dDevice->CreateTexture2D(&stagingTextureDesc, nullptr, &stagingTexture);
    if (FAILED(stagingTextureCreateResult)) {
        std::stringstream error;
        error << "ID3D11Device::CreateTexture2D() failed with 0x" << std::hex << stagingTextureCreateResult;
        captureContext.lastError = error.str();
        return stagingTextureCreateResult;
    }

    captureContext.d3dDeviceContext->CopyResource(stagingTexture, captureTexture);
    captureTexture->Release();

    IDXGISurface* stagingSurface = nullptr;
    HRESULT stagingTextureQiResult = stagingTexture->QueryInterface(__uuidof(IDXGISurface), (void**)&stagingSurface);
    stagingTexture->Release();

    if (FAILED(stagingTextureQiResult)) {
        std::stringstream error;
        error << "Staging texture QueryInterface() failed with 0x" << std::hex << stagingTextureQiResult;
        captureContext.lastError = error.str();
        return stagingTextureQiResult;
    }

    DXGI_MAPPED_RECT mapRect;
    HRESULT mapResult = stagingSurface->Map(&mapRect, DXGI_MAP_READ);
    if (FAILED(mapResult)) {
        std::stringstream error;
        error << "IDXGISurface::Map() failed with 0x" << std::hex << mapResult;
        captureContext.lastError = error.str();
        return mapResult;
    }

    uint8_t* dest = buffer;
    uint8_t* src = mapRect.pBits;
    unsigned int width = captureContext.dxgiOutputDuplicationDesc.ModeDesc.Width;
    unsigned int height = captureContext.dxgiOutputDuplicationDesc.ModeDesc.Height;
    // @todo: currently assumes 32-bit pixel format, could parse this from output duplication desc's format
    unsigned int bytesPerPixel = 4;
    for (unsigned int row = 0; row < height; row++) {
        size_t size = width * bytesPerPixel;
        memcpy(dest, src, size);
        dest += size;
        src += mapRect.Pitch;
    }

    stagingSurface->Unmap();
    stagingSurface->Release();
    captureContext.dxgiOutputDuplication->ReleaseFrame();

    return 0;
}

HRESULT enumerateAdapters(IDXGIFactory1* dxgiFactory, std::vector<IDXGIAdapter1*>& dxgiAdapters) {
    HRESULT result = S_OK;

    unsigned int i = 0;
    while (true) {
        IDXGIAdapter1* dxgiAdapter;
        HRESULT dxgiAdapterEnumerationResult = dxgiFactory->EnumAdapters1(i, &dxgiAdapter);

        // No more adapters found -> break the loop
        if (dxgiAdapterEnumerationResult == DXGI_ERROR_NOT_FOUND) {
            break;
        }

        if (SUCCEEDED(dxgiAdapterEnumerationResult)) {
            dxgiAdapters.push_back(dxgiAdapter);
            i++;
        } else {
            releaseAllAdapters(dxgiAdapters);

            std::stringstream error;
            error << "IDXGIFactory1::EnumAdapters1() failed with  0x" << std::hex << dxgiAdapterEnumerationResult;
            captureContext.lastError = error.str();
            result = dxgiAdapterEnumerationResult;
            break;
        }
    }

    return result;
}

HRESULT enumerateOutputs(IDXGIAdapter1* dxgiAdapter, std::vector<IDXGIOutput1*>& dxgiOutputs) {
    HRESULT result = S_OK;

    unsigned int i = 0;
    while (true) {
        IDXGIOutput* dxgiOutput;
        HRESULT dxgiOutputEnumerationResult = dxgiAdapter->EnumOutputs(i, &dxgiOutput);

        // No more outputs found -> break the loop
        if (dxgiOutputEnumerationResult == DXGI_ERROR_NOT_FOUND) {
            break;
        }

        if (SUCCEEDED(dxgiOutputEnumerationResult)) {
            DXGI_OUTPUT_DESC outputDesc;
            HRESULT dxgiOutputDescResult = dxgiOutput->GetDesc(&outputDesc);

            if (SUCCEEDED(dxgiOutputDescResult) && outputDesc.AttachedToDesktop == TRUE) {
                dxgiOutputs.push_back(reinterpret_cast<IDXGIOutput1*>(dxgiOutput));
            }

            i++;
        } else {
            releaseAllOutputs(dxgiOutputs);

            std::stringstream error;
            error << "IDXGIAdapter1::EnumOutputs() failed with  0x" << std::hex << dxgiOutputEnumerationResult;
            captureContext.lastError = error.str();
            result = dxgiOutputEnumerationResult;
            break;
        }
    }

    return result;
}

HRESULT activateOutputDuplication(IDXGIAdapter1* dxgiAdapter, IDXGIOutput1* dxgiOutput,
    ID3D11Device** d3dDevice, ID3D11DeviceContext** d3dDeviceContext,
    IDXGIOutputDuplication** dxgiOutputDuplication, DXGI_OUTDUPL_DESC *outputDuplicationDesc) {

    D3D_FEATURE_LEVEL featureLevel;
    HRESULT d3dCreateDeviceResult = D3D11CreateDevice(
        dxgiAdapter,
        D3D_DRIVER_TYPE_UNKNOWN,
        nullptr,
        0,
        nullptr,
        0,
        D3D11_SDK_VERSION,
        d3dDevice,
        &featureLevel,
        d3dDeviceContext
    );

    if (FAILED(d3dCreateDeviceResult)) {
        std::stringstream error;
        error << "D3D11CreateDevice() failed with  0x" << std::hex << d3dCreateDeviceResult;
        captureContext.lastError = error.str();
        return d3dCreateDeviceResult;
    }

    HRESULT outputDuplicationResult = dxgiOutput->DuplicateOutput(*d3dDevice, dxgiOutputDuplication);
    if (FAILED(outputDuplicationResult)) {
        (*d3dDevice)->Release();
        (*d3dDeviceContext)->Release();
        std::stringstream error;
        error << "IDXGIOutput1::DuplicateOutput() failed with  0x" << std::hex << outputDuplicationResult;
        captureContext.lastError = error.str();
        return outputDuplicationResult;
    }

    (*dxgiOutputDuplication)->GetDesc(outputDuplicationDesc);

    return S_OK;
}

void releaseAllAdapters(std::vector<IDXGIAdapter1*>& dxgiAdapters) {
    for (size_t i = 0; i < dxgiAdapters.size(); ++i) {
        dxgiAdapters[i]->Release();
    }

    dxgiAdapters.clear();
}

void releaseAllOutputs(std::vector< IDXGIOutput1*>& dxgiOutputs) {
    for (size_t i = 0; i < dxgiOutputs.size(); ++i) {
        dxgiOutputs[i]->Release();
    }

    dxgiOutputs.clear();
}
