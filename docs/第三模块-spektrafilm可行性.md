# 第三模块：spektrafilm（光谱胶片模拟）可行性研究

日期：2026-11-01　对象：<https://github.com/andreavolpato/spektrafilm>（版本 0.3.4，最近提交 2026-06-07）

> 研究方式：只读了源码、README、许可证和依赖清单；**没有在本机运行**（运行外部代码被本环境的安全策略拦下了），所以下面没有实测速度，速度判断来自作者自己在 README 里的说明。

## 1. 它是什么

用胶片厂商数据手册里的光谱数据，按物理过程模拟「相机 RAW → 负片曝光与冲洗 → 放大机印到相纸 → 扫描」的整条链路。不是做一个「胶片风格 LUT」，而是按光谱算：

- 负片：光谱感光度、特性曲线、染料吸收光谱、**成色剂**（遮罩成色剂产生橙色片基、DIR 成色剂提高饱和度和锐度）；
- 空间效果：**颗粒**（随机模型，放大能看到染料云）、**光晕（halation）**、散射、镜头／放大机／扫描仪的模糊、柔焦滤镜；
- 放大机：色温、Y／M 滤色、预闪；扫描：黑白点、USM。

内置 28 个配置（`data/profiles/*.json`）：Kodak Portra 160／400／800（含增感 1／2 档）、Ektar 100、Gold 200、UltraMax 400、Vision3 50D／200T／250D／500T、Ektachrome 100、Kodachrome 64、Verita 200D、Fujifilm C200、Pro 400H、Provia 100F、Velvia 100、Xtra 400；相纸 Portra Endura、Ektacolor Edge、Endura Premier、Supra／Ultra Endura、Fujifilm Crystal Archive Type II；电影正片 2383、2393。

代码分三个包：`spektrafilm`（运行时，线性进、线性出，不依赖界面）、`spektrafilm_gui`（Qt＋napari 桌面界面）、`spektrafilm_lut_creator`（烘焙 `.cube`／`.3dl`／Hald／OCIO 配置）。运行时接口很干净：

```python
from spektrafilm import init_params, simulate
params = init_params(film_profile="kodak_portra_400", print_profile="kodak_portra_endura")
out = simulate(linear_rgb, params)
```

## 2. 许可证（决定怎么接）

| 内容 | 许可证 | 对我们意味着什么 |
|---|---|---|
| 代码（`src/` 三个包） | **GPLv3** | 只要把它的代码和我们的程序**合在一个程序里分发**（同一个进程 import、打进同一个 .app 当库用），整个合并作品就得按 GPLv3 发布。我们的 photo-cull 是 MIT，不能直接 import 进来再按 MIT 发布。作者在 README／CITATION 里还写了「受其方法直接启发的工具也算衍生作品」——这比 GPL 法律上的范围更宽，但代表作者的意愿，应当尊重。 |
| 胶片配置 JSON 和由它生成的 LUT | **CC BY-SA 4.0**（附作者的前言：免费用于任何作品、每份拷贝都署名、不许转卖） | 可以随我们的工具一起发布，前提是：保留作者 Andrea Volpato、来源链接、许可证文本 `SPEKTRAFILM_LICENSE.txt`（作者要求原样不改），改过的要注明谁改了什么；这些 LUT 本身保持 CC BY-SA。和我们 MIT 的代码可以并存（文件各自许可）。 |
| 致谢 | CITATION.cff 的请求 | 在说明和关于页写「film modeling powered by spektrafilm」，学术引用用其 Zenodo DOI。 |

**结论**：「按原文件开源」的做法有两种是干净的：
1. **只用它烘焙出的 LUT**（CC BY-SA），我们的代码仍是 MIT；
2. **把胶片模拟做成单独的 GPLv3 程序**，和 MIT 的 photo-cull 分开放、分开运行（独立进程，通过本地网页接口通信），合在一起发布时属于 GPL 允许的「聚合」，各自许可证不变。

另一个选择是把整个 photo-cull 改成 GPLv3（你是唯一作者，可以改），这样就能直接 import。代价是以后别人基于 photo-cull 做闭源产品就不行了，和当初选 MIT「欢迎提交优化版本」的初衷不完全一致。

## 3. 技术上的硬约束

- **Python 必须是 3.13**（`requires-python = "~=3.13"`，3.14 不行）。你 Mac 上现在是系统 3.9（photo-cull 用）和刚装的 3.12，都不满足 → 第三模块要有自己的环境（推荐用 `uv`，作者也这么推荐，能自动下载 3.13）。
- **依赖很重**：numpy 2.4、scipy、colour-science、scikit-image、matplotlib、numba、OpenImageIO、pyfftw、exiv2、lensfunpy、rawpy，界面还要 PySide6＋napari。光运行时就有几百 MB（numba／llvmlite、OpenImageIO 都不小）。和 photo-cull 现在的 .app 塞在一起会让体积翻好几倍。
- **慢**：作者原话「Full resolution export is very slow at the moment」。光谱计算＋随机颗粒＋多次高斯模糊，预览靠缩小尺寸（`preview_max_size`）。6000 万像素全尺寸可能要几十秒到几分钟。适合「挑出的精选单独出一张胶片版」，不适合批量。
- **项目还在快速变化**：0.3.x，作者说「some areas are still being built and will change fast」，参数结构最近一次重构是 2026-05（GUI refactor with param manifest）。要锁定版本（按 git 提交号）。
- **接口对得上**：它要的是「场景线性、广色域」的输入，可选 `prophotolin`（线性 ProPhoto）——我们的编辑器解码后正好就是线性 ProPhoto，可以直接喂进去；输出选 sRGB。

## 4. 三个方案

| | A. 只用 LUT | B. 独立的胶片模块（GPLv3） | C. photo-cull 整体改 GPLv3 |
|---|---|---|---|
| 做法 | 用 `spektrafilm-lut` 按「sRGB 进 → sRGB 出」烘焙几十个 `.cube`，放进 `luts/spektrafilm/`，在照片编辑里像现有 LUT 一样套用 | 新建 `photo-cull-film`（单独仓库或 `modules/film/` 子目录，GPLv3），自带 3.13 环境，跑 spektrafilm 运行时；一体窗口加第三个页签「胶片冲印」，经本地接口互通 | 直接在 `photo_cull/film/` 里 import spektrafilm |
| 能得到 | 颜色、影调（负片＋相纸的色彩响应） | 全部效果：颗粒、光晕、成色剂、放大机滤色、预闪、扫描 | 同 B |
| 得不到 | 颗粒、光晕等空间效果；按每张照片自动曝光 | — | — |
| 许可证 | 代码 MIT 不变；LUT 为 CC BY-SA，附许可证和署名 | photo-cull 仍 MIT；胶片模块 GPLv3 | 全部 GPLv3 |
| 工作量 | 小（1–2 天：烘焙、命名、署名、编辑器分组） | 中到大（1–2 周：环境安装器、接口、界面、预览缓存、导出队列） | 中（但 Mac 应用要换成 3.13 并打进全部重依赖） |
| Mac 应用 | 不变 | 第三模块单独安装／单独打包，photo-cull 的 .app 检测到它才显示页签 | .app 体积大增，3.9 → 3.13 |
| 风险 | 低 | 上游接口变化、速度 | 许可证变更、体积、速度 |

## 5. 建议

**分两步走：先 A，再 B。**

1. **先做 A（LUT）**：马上就能在照片编辑里用上 Portra、Ektar、Gold、Vision3 等十几种胶片＋相纸组合的颜色，几乎没有风险。
   - 输入 sRGB（对应现在「ST／STD 画面」的约定），输出 sRGB，33³，1-LUT 拓扑；先选 8–12 个常用组合。
   - 每个 `.cube` 文件头写明：作者 Andrea Volpato、来源链接、CC BY-SA 4.0、spektrafilm 版本和提交号、烘焙参数。
   - `luts/spektrafilm/` 里放原样的 `SPEKTRAFILM_LICENSE.txt` 和 `CHANGELOG.txt`（作者要求改动另记）。
   - 编辑器里单独一个分组「spektrafilm（CC BY-SA）」；README 和关于页写「film modeling powered by spektrafilm」。
2. **再做 B（独立的胶片冲印模块）**：
   - GPLv3，单独仓库，README 写明基于 spektrafilm 及其提交号，保留其 LICENSE、SPEKTRAFILM_LICENSE、CITATION。
   - 用 `uv` 建 Python 3.13 环境；安装脚本和 photo-cull 的 `安装环境` 分开。
   - 照片编辑里「发送到胶片冲印」：传线性 ProPhoto 中间图（16 位 TIFF／EXR）和参数，胶片模块出预览（≤ 2K）和全尺寸导出（后台排队）。
   - 先在你的 Mac 上实测速度（24／60 兆像素各一张），再决定是否值得做实时预览。

## 6. 下一步需要你决定

- 选 A、B、C 里的哪一个（或「先 A 再 B」）。
- 如果要做 B：独立仓库（推荐）还是放在 photo-cull 仓库的子目录里（子目录也要单独标 GPLv3）。
- 想先烘焙哪些胶片＋相纸组合。

## 参考

- 仓库：<https://github.com/andreavolpato/spektrafilm>
- 许可证：`LICENSE`（GPLv3）、`SPEKTRAFILM_LICENSE.txt`（CC BY-SA 4.0＋前言）、`CITATION.cff`
- 相关实现：vkdt 的 filmsim 模块（Vulkan）、ART 的 LUT 桥接、Rust 版 spektrafilm-rs、OFX 插件
