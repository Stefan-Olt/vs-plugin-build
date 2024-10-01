# vs-plugin-build

VapourSynth plugin build system for Linux/macOS. It is recommended to use vsrepo to install the plugins.


## Plugin status

Currently most plugins included are simple to compile (no dependencies and standard build system). Other plugins will be added over time (feel free to open pull requests).

## Plugin issues

Not all plugins with build definitions in the repository build correctly on all platforms at the moment:

### linux-glibc-x86_64
-TIVTC: Compile failure (unknown type: `PRIu64`)

### darwin-x86_64
-Bilateral: Linking failure (unknown option: `-Bsymbolic`)
-CAS: Compile failure (needs language features introduced in macOS 10.13)
-IT: Linking failure (unknown option: `-Bsymbolic`)
-JincResize: Crash during test
-MiniDeen: Compile failure (error: argument to `'__builtin_ia32_vec_set_v8hi' must be a constant integer'`)
-NoiseGen: Crash during test
-SmoothUV: Compile failure (error: argument to `'__builtin_ia32_vec_set_v8hi' must be a constant integer'`)
-TIVTC: Compile failure (`malloc.h` not found)

### darwin-aarch64
-Bilateral: configure failure
-DeblockPP7: Uses x86 intrinsics
-DeCross: Only x86 supported
-DeLogo: configure failure (`fatal error: 'vapoursynth/VapourSynth.h' file not found`)
-DePan: configure failure (`fatal error: 'vapoursynth/VapourSynth.h' file not found`)
-IT: configure failure
-JincResize: Crash during test
-NoiseGen: Crash during test
-SmoothUV: Only x86 supported
-TCanny: Crash during test
-TDeintMod: Uses x86 intrinsics
-TemporalSoften2: Only x86 supported
-TIVTC: Only x86 supported
-Yadifmod: Uses x86 intrinsics

### Howto fix build issues:
These are a few ideas how to fix build issues on Darwin/macOS:
-Configure or linking failures: These can most likely be fixed by using a newer (better) build system like meson. Creating a meson.build File for a plugin is very easy, see [here](https://github.com/dubhater/vapoursynth-mvtools/blob/master/meson.build) for an example (with nasm and dependencies).
-Only x86 supported / x86 intrinsics: [sse2neon](https://github.com/DLTcollab/sse2neon) can be used to convert SSE intrinsics to NEON.
