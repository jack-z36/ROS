---
title: "本体参数：RM65系列参数及D-H模型 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/robotParameter/RM65OntologyParameters/"
author:
published: 2026-04-22
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## RM65系列参数及D-H模型

## 基础参数

<table><tbody><tr><th colspan="2">参数名</th><th>参数值</th></tr><tr><th rowspan="13">基础参数</th><th>自由度</th><td>6</td></tr><tr><th>构型</th><td>仿人构型</td></tr><tr><th>关节制动器形式</th><td>1~3关节硬抱闸<br>4~6关节软抱闸</td></tr><tr><th>工作半径/mm</th><td>标准版：610<br>六维力L版：627<br>六维力K版：638.5</td></tr><tr><th>有效负载/kg</th><td>5</td></tr><tr><th>自重/kg</th><td>标准版：7.2<br>六维力版：7.3</td></tr><tr><th>重复定位精度/mm</th><td>±0.05</td></tr><tr><th>TCP线速度/m/s</th><td>≤1.8</td></tr><tr><th>典型功率/W</th><td>≤150</td></tr><tr><th>峰值功率/W</th><td>≤900</td></tr><tr><th>安装角度</th><td>任意角度</td></tr><tr><th>底座尺寸/mm</th><td>φ107</td></tr><tr><th>材质</th><td>铝合金/ABS</td></tr><tr><th rowspan="2">环境适应性</th><th>工作温度/℃</th><td>0-45</td></tr><tr><th>工作湿度</th><td>25~85%无结露</td></tr><tr><th rowspan="6">运动角度范围/°</th><th>J1</th><td>-178~+178</td></tr><tr><th>J2</th><td>-130~+130</td></tr><tr><th>J3</th><td>-135~+135</td></tr><tr><th>J4</th><td>-178~+178</td></tr><tr><th>J5</th><td>-128~+128</td></tr><tr><th>J6</th><td>-360~+360</td></tr><tr><th rowspan="6">最大角速度/ °/s</th><th>J1</th><td>180</td></tr><tr><th>J2</th><td>180</td></tr><tr><th>J3</th><td>225</td></tr><tr><th>J4</th><td>225</td></tr><tr><th>J5</th><td>225</td></tr><tr><th>J6</th><td>225</td></tr><tr><th rowspan="2">力控指标（仅六维力支持）</th><th>六维力量程</th><td>200N/7N·m</td></tr><tr><th>六维力精度</th><td>±0.5%FS</td></tr></tbody></table>

## 本体参数

**MDH模型坐标系：**

![](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM65.png)

**RM65系列MDH参数(改进D-H参数)：**

| joint\_id(i) | $a_{i - 1}$ (mm) | $\alpha_{i - 1}$ (°) | $d_{i}$ (mm) | $\theta_{i}$ / $o f f s e t_{i}$ (°) |
| --- | --- | --- | --- | --- |
| 1 | 0 | 0 | 240.5 | 0 |
| 2 | 0 | 90 | 0 | 90 |
| 3 | 256 | 0 | 0 | 90 |
| 4 | 0 | 90 | 210 | 0 |
| 5 | 0 | \-90 | 0 | 0 |
| 6 | 0 | 90 | $d_{6}$ | 0 |

- RM65-6FB-V: $d_{6} = 184$ mm
- RM65-B-V: $d_{6} = 166.8$ mm
- RM65-B: $d_{6} = 144$ mm
- RM65-6FB: $d_{6} = 161.2$ mm
- RM65-6F: $d_{6} = 172.5$ mm

说明: offset为机械零位与建模零位的偏差, 即 `模型角度 = 关节角度 + offset`.

### RM65系列连杆动力学参数

| joint\_id(i) | 1 | 2 | 3 | 4 | 5 | 6 | \- | \- |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **$m$** | 1.51 | 1.653 | 0.726 | 0.671 | 0.647 | 0.107 | 0.248 | 0.189 |
| **$x$** | 0.491 | 183.722 | 0.029 | 0.007 | 0.032 | \-0.506 | \-0.426 | \-0.352 |
| **$y$** | 7.803 | 0.103 | \-90.105 | \-9.486 | \-83.769 | 0.255 | 0.237 | \-0.067 |
| **$z$** | \-10.744 | \-1.665 | 4.039 | \-8.041 | 2.326 | \-10.801 | \-27.223 | \-18.302 |
| **$L_{x x}$** | 2928.466 | 1711.553 | 7259.884 | 794.014 | 5375.604 | 50.918 | 308.844 | 133.613 |
| **$L_{x y}$** | \-32.63 | \-38.271 | 2.994 | \-0.821 | 2.665 | \-3.136 | \-3.781 | 0.522 |
| **$L_{x z}$** | \-5.816 | 2314.91 | \-0.314 | \-0.655 | \-0.304 | \-0.699 | \-1.468 | 1.623 |
| **$L_{y y}$** | 2506.35 | 70514.722 | 371.872 | 596.235 | 285.265 | 47.42 | 304.616 | 130.260 |
| **$L_{y z}$** | 47.925 | 6.507 | 44.451 | \-34.785 | 14.235 | 0.388 | 0.888 | 0.531 |
| **$L_{z z}$** | 1756.017 | 70036.186 | 7228.758 | 486.228 | 5359.769 | 60.35 | 122.62 | 89.503 |
| **备注** |  |  |  |  |  | B | 6F | 6FB |

说明:

- $m$ 为连杆质量, 单位为 $k g$
- $x$ 为连杆质心x坐标, 单位为 $m m$
- $y$ 为连杆质心y坐标, 单位为 $m m$
- $z$ 为连杆质心z坐标, 单位为 $m m$
- $L_{x x}$,$L_{x y}$,$L_{x z}$,$L_{y y}$,$L_{y z}$,$L_{z z}$ 为连杆坐标系下描述的主惯量, 单位为 $k g \cdot m m 2$
- B: 标准版，6FB: 六维力L版，6F: 六维力K版

备注:

- 以上数据来源为CAD设计值
- 如需质心坐标系下的惯性参数, 使用平行移轴定理即可, 计算方法如下所述.

---

假设有一输出坐标系为坐标系 $\left{\right. i \left.\right}$ ，对齐坐标系 $\left{\right. i \left.\right}$ 的质心坐标系为 $\left{\right. c \left.\right}$ ，质心在坐标系 $\left{\right. i \left.\right}$ 中的坐标为 $P_{c} = \left[\right. x_{c} ， y_{c} ， z_{c} \left]\right.^{T}$ ，则由平行移轴定理可得：

$$
I_{c} = L_{i} - m \left(\right. P_{c}^{T} P_{c} I_{3 \times 3} - P_{c} P_{c}^{T} \left.\right)
$$

式中:

$$
L_{i} = \left[\right. L_{x x} & L_{x y} & L_{x z} \\ L_{x y} & L_{y y} & L_{y z} \\ L_{x z} & L_{y z} & L_{z z} \left]\right.
$$

### 关节分布和尺寸说明

RM65-B机器人本体模仿人的手臂，共有6个旋转关节，每个关节表示1个自由度。如下图所示，机器人关节包括肩部（关节1），肩部（关节2），肘部（关节3），腕部（关节4），腕部（关节5）和腕部（关节6）。

![关节尺寸说明](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM_65_image1.png)

#### 工作空间

RM65-B运动范围，除去基座正上方和正下方的圆柱空间，工作范围为半径610mm的球体。选择机器人安装位置时，务必考虑机器人正上方和正下方的圆柱体空间，尽可能避免将工具移向圆柱体空间。另外，在实际应用中，关节1转动范围：±178°，关节2转动范围：±130°，关节3转动范围：±135°，关节4转动范围：±178°，关节5转动范围：±128°，关节6转动范围：±360°。

![alt text](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM_65_image2.png)

机器人可达空间示意图

从工作空间截面上看，6轴机器人可操作度较好的区域如下图黄色框线示意，在工作空间中整体呈现一个环状区域。

![可操作度较好的区域示意图](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM_65_image3.png)

可操作度较好的区域示意图

  
  

#### 运动奇异点

##### 奇异类型1: 肩部奇异

`当关节5和关节6的轴线交点位于通过关节1轴线且平行关节2轴线的平面上时，产生肩部奇异。`

下图为肩部奇异示意图，蓝色平面即指通过关节1轴线且平行关节2轴线的平面。

![肩部奇异示意图](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM65-00.png)

肩部奇异示意图

  
  

示意点位1：\[90,43.4,-105.7,0,-30,0\]，如下图所示：

![示意点位1](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM_65_image4.png)

示意点位1

示意点位2：\[90,43.4,-105.7,0,62.3,0\]，如下图所示：

![示意点位2](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM_65_image5.png)

示意点位2

##### 奇异类型2：肘部奇异

`当关节5和关节6的轴线交点位于由关节2和关节3的轴线组成的平面上时，q3=0，即点位格式为[x,x,0,x,x,x]，产生肘部奇异。`

示意点位1：\[-90,60,0,0,90,0\]，如下图所示：

![示意点位1](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM_65_image6.png)

示意点位1

示意点位2：\[0,0,0,90,-60,0\]，如下图所示：

![示意点位2](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM_65_image7.png)

示意点位2

##### 奇异类型3：腕部奇异

`当关节4和关节6的轴线平行时，q5=0，即点位格式为[x,x,x,x,0,x]，产生腕部奇异。`

示意点位1：\[0,60,30,0,0,0\]，如下图所示：

![示意点位1](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM_65_image9.png)

示意点位1

  
  

##### 奇异类型4：边界奇异

`当机械臂末端到达最远端时，q3=0且q5=0，即点位格式为[x,x,0,x,0,x]，产生边界奇异。`

示意点位1：\[0,0,0,0,0,0\]，如下图所示：

示意点位1

示意点位2：\[-90,90,0,0,0,0\]，如下图所示：

![示意点位2](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM_65_image11.png)

示意点位2

示意点位3：\[-90,45,0,0,0,0\]，如下图所示：

![示意点位3](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM_65_image12.png)

示意点位3

  
  

#### 负载曲线图

下图分别表示RM65-B、RM65-6F和RM65-6FB机械臂末端负载曲线图。其中L是末端负载的质心相对于末端法兰平面的径向距离，Z是相对于末端法兰平面的法向距离。

![RM65-B](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM_65_image13.png)

RM65-B机械臂末端负载曲线图

![RM65-6F](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM_65_image14.png)

RM65-6F机械臂末端负载曲线图

![RM65-6FB](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/robotParameter/RM65OntologyParameters/RM_65_imageFB.png)

RM65-6FB机械臂末端负载曲线图
