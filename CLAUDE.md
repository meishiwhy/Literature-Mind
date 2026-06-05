# Research Design: Carbon Plate Shoes & Flatfoot Landing Kinematics

## Experimental Design
- **Design**: 2×2 mixed factorial
  - FootType (between-subject): Normal arch (n=14) vs Flatfoot (n=12)
  - Shoe (within-subject): CS (carbon plate, 5.76 N·m) vs NS (regular, 2.86 N·m)
- **Task**: 45 cm bilateral drop jump landing
- **Lab**: Shandong Sport University Biomechanics Lab

## Motion Model
- **Software**: Visual3D
- **Model**: Self-built 7-segment IOR foot model (R_new_model.mdh)
- **Segments**: RPV, RTH/LTH, RSK/LSK, RMET/LMET, RMid/LMid, RCal/LCal, RFT/LFT + RHal/LHal (hallux)
- **Hallux segment**: 3-marker (R_FM1, R_PM6, R_FM5) — independent 3D rigid segment

## Joint Angles Defined
| Joint | Definition | Planes |
|---|---|---|
| ANKLE | RSK → RFT | FLEX (sagittal), ABD (frontal=inversion/eversion), ROT (transverse) |
| A_MTP | RHal → RMET (anatomical MTP) | FLEX, ABD, ROT |
| F_MTP | RHal → RFT (functional MTP) | FLEX, ABD, ROT |
| GRF | Ground reaction force | X/Y/Z |

## Coordinate System (Lab)
- X (ML): +Right, -Left
- Y (AP): +Anterior, -Posterior  
- Z (Axial): +Superior, -Inferior
- Joint rotations: X=Flexion(+)/Extension(-), Y=ABD/Adduction, Z=Internal(+)/External(-) rotation

## Statistical Analysis
- **SPM** (Statistical Parametric Mapping): 2×2 ANOVA on continuous time series (0-100% stance)
- **SPSS discrete**: high_peak, low_peak, high_diff, low_diff, PeakTime

## Core Findings
1. **ANKLE_ABD** (frontal plane): Strong foot-type × shoe interaction (SPM p<0.001, 0-99% stance) — the strongest signal
2. **ROM restriction**: Flatfoot shows reduced sagittal & transverse plane ROM regardless of shoe
3. **MTP modulation**: Phase-specific carbon plate effect in flatfoot (21-45% stance)
4. **Kinematic-kinetic decoupling**: GRF shows no significant differences across conditions

## Literature (most relevant)
- **Stone et al. 2024**: MFM comparison of foot types, limited dynamic differences in walking
- **Portinaro et al. 2014**: Modified Rizzoli foot model for pes planus diagnosis
- **Chang et al. 2012**: Flatfoot vs normal arch in drop landings
- **Haelewijn et al. 2025**: Symptomatic flatfoot in running & drop-hop
- **Luo et al. 2025**: "Distal restriction-proximal compensation" mechanism of carbon plate shoes

## Skills

### LitMind
- **[litmind-zotero](litmind/.claude/skills/litmind-zotero/SKILL.md)**: Zotero Connector — 导出文献元数据
- **[litmind-parser](litmind/.claude/skills/litmind-parser/SKILL.md)**: Paper Parser — PDF 解析与结构化
- **[litmind-analyzer](litmind/.claude/skills/litmind-analyzer/SKILL.md)**: Paper Analyzer — LLM 论文知识提取
- **[litmind-knowledge](litmind/.claude/skills/litmind-knowledge/SKILL.md)**: Knowledge Base — 存储与索引科研知识
- **[litmind-chat](litmind/.claude/skills/litmind-chat/SKILL.md)**: Research Chat — 科研知识库问答
- **[litmind-evidence](litmind/.claude/skills/litmind-evidence/SKILL.md)**: Evidence Finder — 科研证据检索与归纳
- **[litmind-review](litmind/.claude/skills/litmind-review/SKILL.md)**: Review Generator — 基于科研知识库的综述生成系统
- **[litmind-discussion](litmind/.claude/skills/litmind-discussion/SKILL.md)**: Discussion Generator — 基于证据的 Discussion 草稿生成
