# 新建扫描任务 — 向导弹窗设计参考

## 结构

```
modal-overlay（遮罩，blur 背景）
└── modal-panel（600px 宽，圆角 14px，flex 纵向三段式）
    ├── modal-header（标题 + 关闭按钮）
    ├── wizard-steps（步骤指示器，浅灰底，border-bottom 分隔）
    ├── modal-body（可滚动内容区）
    └── modal-footer（浅灰底，取消左 / 操作按钮右）
```

## 步骤流程

**单文件扫描（2 步）**
1. 选择文件 → 虚线拖拽上传区
2. 扫描参数 → 脱敏开关 + 置信度阈值滑条

**文件夹扫描（3 步）**
1. 基本信息 → 任务名称 + 路径输入（含"浏览"按钮调用原生文件夹对话框）
2. 文件筛选 → 4 类文件类型卡片（文档/图片/文本/压缩包），每类可展开勾选具体扩展名
3. 扫描参数 → 同单文件

## CSS 关键类

| 类名 | 职责 |
|------|------|
| `.modal-overlay` | 固定定位遮罩，flex 居中，`backdrop-filter: blur` |
| `.modal-panel` | `width:600px; max-height:88vh; overflow:hidden` |
| `.modal-header` | `padding:20px 28px; border-bottom` |
| `.modal-body` | `padding:24px 28px; overflow-y:auto; flex:1` |
| `.modal-footer` | `padding:16px 28px; background:var(--bg-side); border-radius:0 0 14px 14px` |
| `.wizard-steps` | 步骤条容器，`background:var(--bg-side); border-bottom` |
| `.wstep` / `.wstep-num` / `.wstep-line` | 步骤圆点（30px）+ 连接线（56px），done 态绿色 ✓ |
| `.form-group` | 表单组，`margin-bottom:20px`，label 粗体，input 全宽 |
| `.input-row` | 输入框 + 按钮水平排列，input flex 撑满 |
| `.file-upload-zone` | 虚线拖拽区，hover 变蓝底，`padding:28px 20px` |
| `.file-type-categories` / `.file-type-cat` | 文件类型卡片，选中态描边+浅蓝底+阴影 |
| `.ftags` / `.ftag` | 扩展名标签，选中态蓝底白字 |
| `.footer-actions` | 底部按钮组 `display:flex; gap:8px` |

## 行为

- 点击遮罩空白区关闭弹窗
- 步骤切换用 `wizardNext()` / `wizardPrev()`，单文件模式自动跳过步骤 2
- "浏览"按钮调用 `POST /api/v1/scan/browse-folder`（tkinter 原生对话框）
- 文件上传通过 `POST /api/v1/scan/upload`，返回服务器路径
- 开始扫描调用 `POST /api/v1/scan/start`，轮询状态直到完成
