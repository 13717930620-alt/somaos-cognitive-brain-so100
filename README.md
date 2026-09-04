# SomaOS Cognitive Brain — 人形机器人集成版 (Robonix Community Entry)

> 本仓库为 Robonix 社区收录用「闭源部署目录」: 元数据 (robonix_manifest.yaml) +
> 可运行 demo 包 (demos/) + 容器构建与运行说明 (docker/) + 本 README。
> **不含源码 / 模型权重 / 训练数据 / 协议细节 / 内部基准数据。**

---

## 平台与验证状态 (Platform & Validation Status)

| 项 | 状态 |
|---|---|
| 目标平台 (Target) | 双足人形机器人 (头/躯干/双臂/双足/灵巧手全身协调载体) |
| 验证状态 (Validation) | **仅仿真验证 (simulation only)** — 调度与感知-决策回路已在仿真环境闭环运行 |
| 真机状态 (Real robot) | **尚未在人形真机部署** — 真机集成进行中 |
| 计算环境 (仿真) | x86 桌面 + GPU, Windows 11 / Ubuntu 22.04 |
| 证据形式 | ① 本仓库可运行 demo (固定种子, 结果可复现) ② 闭源二进制运行时 (GitHub Release [v1.0.0-bin](https://github.com/13717930620-alt/somaos-cognitive-brain-so100/releases/tag/v1.0.0-bin), `node loader.js health` 自检通过) ③ 闭源容器 (demo/ service 双模式) |

---

## 可运行演示 (Runnable Demos — clone 即跑)

零依赖 (纯 Python 标准库, 3.8+), 固定种子结果可复现。核心算法为闭源,
demo 中以简化替代实现展示**框架逻辑** (调度框架 / 决策状态机 / 反射覆盖),
详见 [demos/README.md](demos/README.md)。

```bash
# 演示 1: 多脑区任务优先级调度 (安全级任务抢占 + 全部按期完成)
python demos/task_priority/demo_task_priority.py --seed 7 --ticks 40

# 演示 2: 感知→决策→指令回路 (IMU 姿态突变触发 SAFE_HOLD 反射并恢复)
python demos/perceive_decide/demo_perceive_decide.py --seed 11 --frames 24
```

实测输出 (节选, seed=7 / seed=11 确定性可复现):

```
t14  PREEMPT  joint_command_stream <-> balance_reflex on MOTOR
summary: finished=10/10  preemptions=1  missed_deadlines=0

f12 roll=+31.0deg -> SAFE_HOLD (reflex: instability) cmd=FREEZE_ALL posture=CROUCH_SAFE
summary: state_hist={'WALK': 12, 'SAFE_HOLD': 2, 'IDLE': 6, 'REACH': 4}
```

---

## 闭源二进制运行时 (GitHub Release — 下载即跑, 免源码)

完整认知脑运行时已编译为 V8 字节码发布 (无任何可读源码 / 权重 / 凭据):

1. 从 [Release v1.0.0-bin](https://github.com/13717930620-alt/somaos-cognitive-brain-so100/releases/tag/v1.0.0-bin)
   下载 `somaos-cognitive-brain-humanoid-bin-1.0.0.zip` (约 35 MB)
2. 解压后仅需 Node.js 18+ (依赖已内置):

```bash
# 健康自检: 启动 19 脑区完整大脑, 输出 JSON 状态后退出
node loader.js health
```

实测自检输出 (确定性):

```json
{
  "status": "healthy",
  "healthy": true,
  "regionCount": 19,
  "lifeSupport": true
}
```

其他模式: `node loader.js brain-only` (仅脑区架构) / `node loader.js`
(完整启动, Web UI 监听 127.0.0.1:3000)。模型相关子系统在无权重环境下
自动降级到内置确定性后端, 详见包内 RUN.md。

---

## 部署 (闭源容器)

完整系统以编译后二进制形式发布为容器镜像 (源码与权重不出维护者环境):

```bash
# demo 模式 — 自包含, 无需权重, 输出完整调度/决策回路
docker run --rm ghcr.io/13717930620-alt/somaos-cognitive-brain:latest

# service 模式 — 启动闭源认知运行时 (权重启动时从维护者受控源拉取, sha256 校验)
docker run --rm -e SOMAOS_WEIGHT_URL="..." -e SOMAOS_WEIGHT_SHA256="..." \
  -p 8765:8765 ghcr.io/13717930620-alt/somaos-cognitive-brain:latest --mode service
```

镜像构建保证: 构建阶段将私有源码编译为二进制扩展, 运行阶段仅含编译产物
(源码层在阶段边界丢弃); 权重永不打入镜像。详见
[docker/install.md](docker/install.md)。

---

## 项目一句话定位

**SomaOS Cognitive Brain (SomaOS 认知意识分册)** 是一个面向**双足人形机器人**的「**生成分区双脑协同控制内骨干**」。
"新皮层分区推进 + 双脑协同锚定 + 脑核安全制动"三层脑模型提取为可在通用计算硬件上运行的工程结构。
设计金句: **双脑分离 + 内生安全层 + 涌现分层执行**。

---

## 为何 SomaOS Cognitive Brain 不只是又一个 LLM+人形机器人

| 常见 VLA-ROS2 适配方案的问题 | SomaOS 的结构化优势 |
|---|---|
| 世界模型异义: 感知模块"看见了"一个杯子、认知层却理应为'我要把面前的瓶子拿起'、运动模块却完全不同的方向 | **三相时序一致性闭环结构** |
| 暗箱信任: VLA 模型自我评估置信度常为 99% 却做错事、外部无独立判断 | **语义-意图双层评估体系** |
| 安全靠外挂: CBF/约束层是独立实现，与决策层不同步、边界死锁频发 | **内生双路径门控**: 决策前慢链路+执行前快链路 同一脑核内部共 |
| 长任务断链: 超过 7-10 秒的子目标序列因状态异义而断链 | **情景-语义双层记忆 + 子目标回退** |
| 运行时不优化: 固定权重部署，失败经验只会重复发生不会自动调整 | **内在渐进式接口自调谐** |

---

## 核心技术主栈 (概念层白皮书 · 不含任何实现细节)

> 以下描述全部为「公开可说明的算法层级技术主栈」。
> 它们用于对外阐明技术差异定位, 不涉及任何代码结构、服务权重、参数配置、字段定义、内部接口协议等技术信息。

### 栈1 三相时序一致性闭环结构 (Three-Phase Anchoring Closed Loop)

### 栈2 语义-意图双层评估体系

### 栈3 内生双路径门控

### 栈4 情景-语义双层记忆 + 子目标回退

### 栈5 内在渐进式接口自调谐

---

## 对外接口

- **标准**: RCAN 指令入口、本地 HTTP 控制接口、本地 LLM 推理接口、ESTOP 制动主线路输入、状态事件回传
- **部署方式**: 独立 robot entry，与 motor_brain 协同使用 RCAN 语义接口层对接

---

## 平台说明

- **适用硬件**: 双足人形机器人 (全身协调驱动系列; 带头/躯干 双臂/双腿/双足的多自重载体人形机体)
- **推荐算力**: Jetson Orin 系列/ x86 桌面 + GPU 加速卡 (本地 LLM 推理时需 运动控制本身单机能跑)
- **操作系统**: Linux (推荐 Ubuntu 22.04+); Windows 开发环境可用

---

## 许可证

MulanPSL-2.0
