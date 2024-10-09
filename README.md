# vs-plugin-build

[VapourSynth](https://www.vapoursynth.com/) plugin build system for Linux/macOS. It is recommended to use [vsrepo](https://github.com/vapoursynth/vsrepo/) to install the plugins.
Currently most plugins included are simple to compile (no dependencies and standard build system). Other plugins will be added over time (feel free to open pull requests).

## Plugin compatibility

Default requirements:
- linux-glibc-x86_64 (Linux 64-Bit): libc6 at least 2.17, Linux Kernel at least 3.2.101 (compiled with GCC 11)
- darwin-x86_64 (Intel Mac): At least OS X 10.11 El Capitan
- darwin-aarch64 (Apple Silicon Mac): At least macOS 11 Big Sur

If a plugin has higher or other requirements this is shown in the list.

## Plugin list

For each category the number of currently available plugins in this repo and the total number of plugins in vsrepo is given.
For a nice list of all plugins (and scripts/wheels) with more details, see the [VapourSynth Database](https://vsdb.top/vsrepogui).

|Name                                                        |  Linux (x86_64)  | macOS (Intel) |macOS (Apple Silicon)|
|------------------------------------------------------------|------------------|---------------|---------------------|
|<td colspan="3">**Color/Levels (2/5)**
|[Curve](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-Curve)|        ✅         |      ✅      |      ✅       |
|[MatchHistogram](https://github.com/dubhater/vapoursynth-matchhistogram)|        ✅         |      ✅      |      ✅       |
|<td colspan="3">**Deinterlacing (6/10)**
|[Bwdif](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-Bwdif)        |        ✅         |      ✅      |      ✅       |
|[EEDI2](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-EEDI2)        |        ✅         |      ✅      |      ✅       |
|[NNEDI3](https://github.com/dubhater/vapoursynth-nnedi3)                        |        ✅         |      ✅      |      ✅       |
|[SangNom](https://github.com/dubhater/vapoursynth-sangnom)                      |        ✅         |      ✅      |      ✅       |
|[TDeintMod](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-TDeintMod)|        ✅         |      ✅      |      ❌       |
|[Yadifmod](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-Yadifmod)  |        ✅         |      ✅      |      ❌       |
|<td colspan="3">**Denoising (11/38)**
|[Bilateral](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-Bilateral)|        ✅         |      ❌      |      ❌       |
|[BM3D](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-BM3D)          |        ✅         |      ✅      |      ✅       |
|[Cnr2](https://github.com/dubhater/vapoursynth-cnr2)                            |        ✅         |      ✅      |      ✅       |
|[degrainmedian](https://github.com/dubhater/vapoursynth-degrainmedian)          |        ✅         |      ✅      |      ✅       |
|[FluxSmooth](https://github.com/dubhater/vapoursynth-fluxsmooth)                |        ✅         |      ✅      |      ✅       |
|[Frfun7](https://github.com/dubhater/vapoursynth-frfun7)                        |        ✅         |      ✅      |      ✅       |
|[HQDn3D](https://github.com/theChaosCoder/vapoursynth-hqdn3d)                   |        ✅         |      ✅      |      ✅       |
|[MiniDeen](https://github.com/dubhater/vapoursynth-minideen)                    |        ✅         |      ❌      |      ✅       |
|[TBilateral](https://github.com/dubhater/vapoursynth-tbilateral)                |        ✅         |      ✅      |      ✅       |
|[TemporalMedian](https://github.com/dubhater/vapoursynth-temporalmedian)        |        ✅         |      ✅      |      ✅       |
|[TemporalSoften2](https://github.com/dubhater/vapoursynth-temporalsoften2)      |        ✅         |      ✅      |      ❌       |
|<td colspan="3">**Dot Crawl and Rainbows (6/8)**
|[Bifrost](https://github.com/dubhater/vapoursynth-bifrost)  |        ✅         |      ✅      |      ✅       |
|[DeCross](https://github.com/dubhater/vapoursynth-decross)  |        ✅         |      ✅      |      ❌       |
|[DeDot](https://github.com/dubhater/vapoursynth-dedot)      |        ✅         |      ✅      |      ✅       |
|[SmoothUV](https://github.com/dubhater/vapoursynth-smoothuv)|        ✅         |      ❌      |      ❌       |
|[SSIQ](https://github.com/dubhater/vapoursynth-ssiq)        |        ✅         |      ✅      |      ✅       |
|[TComb](https://github.com/dubhater/vapoursynth-tcomb)      |        ✅         |      ✅      |      ✅       |
|<td colspan="3">**Inverse Telecine (2/3)**
|[IT](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-IT)|        ✅         |      ❌      |      ❌       |
|[TIVTC](https://github.com/dubhater/vapoursynth-tivtc)            |        ✅         |      ✅      |      ❌       |
|<td colspan="3">**Other (21/75)**
|[AddGrain](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-AddGrain)        |        ✅         |      ✅      |      ✅       |
|[AWarpSharp2](https://github.com/dubhater/vapoursynth-awarpsharp2)                    |        ✅         |      ✅      |      ✅       |
|[CTMF](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-CTMF)                |        ✅         |      ✅      |      ✅       |
|[Deblock](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-Deblock)          |        ✅         |      ✅      |      ✅       |
|[DeblockPP7](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-DeblockPP7)    |        ✅         |      ✅      |      ❌       |
|[DeLogo](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-DeLogo)            |        ✅         |      ✅      |      ❌       |
|[DePan](https://github.com/Vapoursynth-Plugins-Gitify/DePan)                          |        ✅         |      ✅      |      ❌       |
|[FieldHint](https://github.com/dubhater/vapoursynth-fieldhint)                        |        ✅         |      ✅      |      ✅       |
|[fillborders](https://github.com/dubhater/vapoursynth-fillborders)                    |        ✅         |      ✅      |      ✅       |
|[Histogram](https://github.com/dubhater/vapoursynth-histogram)                        |        ✅         |      ✅      |      ✅       |
|[LGhost](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-LGhost)            |        ✅         |      ✅      |      ✅       |
|[Median](https://github.com/dubhater/vapoursynth-median)                              |        ✅         |      ✅      |      ✅       |
|[MotionMask](https://github.com/dubhater/vapoursynth-motionmask)                      |        ✅         |      ✅      |      ✅       |
|[MSmoosh](https://github.com/dubhater/vapoursynth-msmoosh)                            |        ✅         |      ✅      |      ✅       |
|[MVTools](https://github.com/dubhater/vapoursynth-mvtools)                            |        ✅         |      ✅      |      ✅       |
|[NoiseGen](https://github.com/theChaosCoder/vapoursynth-noisegen)                     |        ✅         |      ❌      |      ❌       |
|[RemapFrames](https://github.com/Irrational-Encoding-Wizardry/Vapoursynth-RemapFrames)|        ✅         |      ✅      |      ✅       |
|[Retinex](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-Retinex)          |        ✅         |      ✅      |      ✅       |
|[TCanny](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-TCanny)            |        ✅         |      ✅      |      ❌       |
|[TEdgeMask](https://github.com/dubhater/vapoursynth-tedgemask)                        |        ✅         |      ✅      |      ✅       |
|[vs-noise](https://github.com/wwww-wwww/vs-noise)                                     |        ✅         |      ✅      |      ✅       |
|<td colspan="3">**Resizing and Format Conversion (3/13)**
|[Descale](https://github.com/Jaded-Encoding-Thaumaturgy/vapoursynth-descale)|        ✅         |      ✅      |      ✅       |
|[JincResize](https://github.com/Kiyamou/VapourSynth-JincResize)             |        ✅         |      ❌      |      ❌       |
|[Tonemap](https://github.com/ifb/vapoursynth-tonemap)                       |        ✅         |      ✅      |      ✅       |
|<td colspan="3">**Sharpening (2/2)**
|[ASharp](https://github.com/dubhater/vapoursynth-asharp)                                           |        ✅         |      ✅      |      ✅       |
|[CAS - Contrast Adaptive Sharpening](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-CAS)|        ✅         |  ✅ (10.13)  |      ✅       |
|<td colspan="3">**Source/Output (4/13)**
|[BestSource](https://github.com/vapoursynth/bestsource)      |        ✅         |  ✅ (10.15)  |      ✅       |
|[ColorBars](https://github.com/ifb/vapoursynth-colorbars)    |        ✅         |      ✅      |      ✅       |
|[FFmpegSource2](https://github.com/FFMS/ffms2)               |        ✅         |      ✅      |      ✅       |
|[QRCodeSource](https://github.com/jeremypoulter/QRCodeSource)|        ✅         |      ✅      |      ✅       |
|<td colspan="3">**Subtitles (0/5)**


## Plugin issues

Not all plugins with build definitions in the repository build correctly on all platforms at the moment:

### linux-glibc-x86_64
*currently all plugins can be build*

### darwin-x86_64
- Bilateral: Linking failure (unknown option: `-Bsymbolic`)
- IT: Linking failure (unknown option: `-Bsymbolic`)
- JincResize: Crash during test
- MiniDeen: Compile failure (error: argument to `'__builtin_ia32_vec_set_v8hi' must be a constant integer'`)
- NoiseGen: Crash during test
- SmoothUV: Compile failure (error: argument to `'__builtin_ia32_vec_set_v8hi' must be a constant integer'`)

### darwin-aarch64
- Bilateral: configure failure
- DeblockPP7: Uses x86 intrinsics
- DeCross: Only x86 supported
- DeLogo: configure failure (`fatal error: 'vapoursynth/VapourSynth.h' file not found`)
- DePan: configure failure (`fatal error: 'vapoursynth/VapourSynth.h' file not found`)
- IT: configure failure
- JincResize: Crash during test
- NoiseGen: Crash during test
- SmoothUV: Only x86 supported
- TCanny: Crash during test
- TDeintMod: Uses x86 intrinsics
- TemporalSoften2: Only x86 supported
- TIVTC: Only x86 supported
- Yadifmod: Uses x86 intrinsics

### Howto fix build issues:
These are a few ideas how to fix build issues on Darwin/macOS:
- Configure or linking failures: These can most likely be fixed by using a newer (better) build system like meson. Creating a meson.build File for a plugin is very easy, see [here](https://github.com/dubhater/vapoursynth-mvtools/blob/master/meson.build) for an example (with nasm and dependencies).
- Only x86 supported / x86 intrinsics: [sse2neon](https://github.com/DLTcollab/sse2neon) can be used to convert SSE intrinsics to NEON. *sse2neon can also be used to convert SSE code to NEON for plugins that can be build on aarch64 (Apple Silicon) to improve performance.* 

If you like to help fixing these issues it is recommended that you open an issue on the plugin repository (or create an pull request that fixes the issue there) with the hope the author will release a new version with a fix. If the plugin is unmaintained (or the maintainer does not respond) you can may open an issue here, so the patch can be included in the build system (less desirable option).
