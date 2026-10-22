# 家教备课出题助手

面向 Codex 的家教工作流 Skill。英文调用名：`high-school-math-tutor`。候选版本：`0.1.0-beta`，尚未执行 GitHub 发布。

支持高中数学、物理及后续学科的备课、讲义与教案、练习和试卷、教师解析、证据式错题分析及学生档案维护。它是指令、模板和校验脚本的组合，需要宿主模型与相应工具执行任务，不是独立教学管理软件。

## 功能与边界

| 场景 | 所需能力 | 边界 |
|---|---|---|
| 通用讲解、教案、讲义草稿 | Codex | 不绑定学生也可使用；实际输出必须复核 |
| 真题与模拟题 | Firecrawl或其他可靠联网检索 | 摘要不等于核验；必须核对原卷、题号、分值、图形和答案 |
| Word/PDF/Excel | 对应文档技能或可用处理库 | 本包不安装依赖、不保证宿主具备渲染能力 |
| 学生历史档案 | 自行连接的Google Drive或用户授权资料 | 默认未配置；无权限时如实报告，不使用他人档案 |
| 分值清单检查 | Python 3.9+，只用标准库 | 不证明题源真实、答案正确或地区合规 |

安装本包不会连接账号、安装插件、创建学生档案、设置磁盘目录或建立后台同步。Google Drive和Firecrawl均不是文字讲解的必需条件。需要其能力时由使用者自行连接授权，只调用当前任务必要工具。

## 目录

```text
README.md
CHANGELOG.md
VERSION
.gitignore
skills/high-school-math-tutor/
  SKILL.md
  agents/openai.yaml
  references/
  templates/
  scripts/check_exam.py
examples/
tests/
```

## 安装

本仓库按本地Skill目录方式提供。下载并解压仓库后，将 `skills/high-school-math-tutor` 复制到自己的 `~/.agents/skills/`，保留同名目录。不要把整个仓库根目录当作 Skill，也不要覆盖已有同名技能。

Windows：在解压后的仓库根目录打开普通PowerShell，执行：

```powershell
$skillSource = Join-Path (Get-Location) 'skills\high-school-math-tutor'
$skillTarget = Join-Path $env:USERPROFILE '.agents\skills\high-school-math-tutor'
if (-not (Test-Path -LiteralPath (Join-Path $skillSource 'SKILL.md'))) { throw '请先进入解压后的仓库根目录' }
if (Test-Path -LiteralPath $skillTarget) { throw '已存在同名Skill，请先比较版本，不覆盖安装' }
New-Item -ItemType Directory -Path (Split-Path -Parent $skillTarget) -Force | Out-Null
Copy-Item -LiteralPath $skillSource -Destination $skillTarget -Recurse
```

也可以在仓库公开后请求Codex：

> 使用 $skill-installer 从 https://github.com/ti0874533-prog/high-school-math-tutor 的 skills/high-school-math-tutor 目录安装 Skill，已有同名版本时先停止并比较。

安装后尝试 `$high-school-math-tutor`；若未显示，重载Codex。自然语言可由description匹配，但本包没有验证所有宿主、新会话及表述的自动触发效果。安装位置及调用方式参考[官方技能文档](https://learn.chatgpt.com/docs/build-skills)。若进一步作为可安装产品分发，可按官方说明另行打包为插件；本候选包尚未包含插件清单或连接器。

## 第一次使用：不需要先接入云端

可以直接输入：

> $high-school-math-tutor 为高中数学“直线与圆”写一份文字复习讲义草稿，包含知识梳理、两道原创例题和教师解析，不查询学生档案、不生成文件。

> 帮我备课：高中物理牛顿运动定律，给通用讲解顺序、易错点和达标条件，不绑定具体学生。

需要真实题源时明确考试年份、地区、知识范围和题型。默认发现策略为小红书公开内容优先，不可访问时回退可靠公开来源；正式模拟题按深圳→广东其他地区→当年新高考Ⅰ卷地区→Ⅱ卷地区筛选，北京、浙江只允许符合条件的高考真题。卷别按实际年份、地区和科目核实，不使用永久省份名单代替核对。

## 配置自己的本地工作区

公开配置 `references/local-storage.json` 的 `workspace_config` 为 `null`，没有作者盘符或目录。未配置时生成文件应先确认位置；用户本次明确指定的输出路径优先。

1. 在仓库和Skill目录之外选一个自己的私人工作区。
2. 将[配置示例](examples/workspace.example.json)复制到该私人工作区，命名为 `workspace.json`，按需调整。示例不会创建目录。
3. 在对话中明确提供该配置文件的路径并授权用于本任务。路径中的相对项以配置文件所在目录为基准。
4. 后续新对话若没有取得该配置路径，应重新提供；本包不承诺跨会话记忆或自动持久发现配置。

本地索引只保存定位元数据，按学生编号、科目和模块筛选再开文件；大型PDF先定位页码。索引需要随新文件维护，本包不包含后台扫描器或自动更新服务。

## 配置自己的Google Drive

公开 `references/archive-locations.json` 的真实ID、链接和本地根目录都为空，`primary_storage` 为 `null`，状态为 `unconfigured`。安装不代表云端已经存在任何目录或学生。

先连接自己的Google Drive。已有档案时，在对话中提供自己授权的根目录及学生总索引链接；也可以将该空配置复制到仓库和Skill之外的私人文件，填写自己的地址后提供其路径。不要将私人配置写回公开Skill或提交仓库，不存令牌、密码或登录凭据。

索引一行对应“学生编号＋科目”，至少建议包含：学生编号、学生代号、科目、年级、当前知识模块、当前教学进度、最近一次上课日期、最近一次检测情况、下一阶段教学目标、学生档案链接、最后更新时间。

没有现有云端系统时，先展示拟创建内容并取得确认，不能把本地目录说成已上传。读成功不能证明写权限。写入长期记录前展示具体差异并获得明确确认，提交前重读基线，写后回读并记录日志；多文件一致性仍需逐项验证。没有双向自动同步，也不会自动批量下载云端档案。

## 运行结构检查

在仓库根目录执行：

```text
python -B skills/high-school-math-tutor/scripts/check_exam.py examples/exam-manifest.example.json
python -B -m unittest discover -s tests -v
```

示例是没有题面的原创结构数据，不是真题或学生记录。`check_exam.py` 只校验结构、年份范围、分值及部分题源字段；`verified: true` 本身不能证明已核验。标准Skill校验器如需PyYAML，应在使用者自己的开发环境安装，不是运行分值脚本的依赖。

## 验证状态与已知限制

- 个人版曾完成三道真题检索、独立求解、PDF生成及学生档案读取；这些个人数据、题目文件及云端配置均不随包分发。
- 公开包新增的空配置、结构、资源引用、隐私排除和脚本回归以同版本 `RELEASE_CHECKS.json` 为准。这些检查不是外部新用户完整教学流程测试。
- 完整讲义生成、真实错题诊断、多学生多科目长期更新、云端版本冲突和新会话隐式调用尚未完成公开版本端到端验收。
- 小红书优先发现不意味着可以成功读取任意笔记；不绕过登录、验证码或访问限制。
- 地区准入与答案复核目前依赖流程执行，分值脚本没有自动强制地区筛选或联网验真能力。
- 不打包历史试卷、第三方PDF、学生资料或个人测试报告；旧产物不能作为当前地区规则合格样例。
- 不自动删除档案、联系家长、申请订单。学生信息仅记录必要部分，未知内容保持待补充。

## 许可证与发布

本候选包不替作者选择许可证，也不包含 `LICENSE`。发布前由作者确认仓库已有许可证或另行选择；在此之前不要将它宣称为已授权任意使用、修改和再分发的开源发行版。第三方题目和资料不因本项目许可证而自动获得再分发授权。

上传前只选本候选仓库内容，保留或核对远程已有README、LICENSE与.gitignore，不上传个人工作区、学生文件、私人配置和外层本机交付说明。推荐先私有检查，再决定公开。本包没有执行git push、创建Release或更改远程设置。
