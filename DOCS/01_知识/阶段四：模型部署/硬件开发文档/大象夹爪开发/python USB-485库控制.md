---
title: "python USB-485库控制"
source: "https://docs.elephantrobotics.com/docs/myGripper-F100-cn/6-SDKDevelopment/6.2.html"
author:
published:
created: 2026-06-08
description:
tags:
  - "clippings"
---
**USB-485模块接线** ：

连接夹爪端的 24V，GND, 485\_A(T/R+,485+), 485\_B(T/R-,485-)共 4 根线，电源为24V直流稳压电源，将模块的 USB 插口插入到电脑的 USB 接口

![](https://docs.elephantrobotics.com/docs/myGripper-F100-cn/img/new485c.jpg)

485A 接入 485 转 USB 模块 A+;  
485B 接入 485 转 USB 模块 B-;  
24V 接入 24V 直流稳压电源正极;  
GND 接入 24V 直流稳压电源负极

**驱动库安装**

[点击下载驱动库](https://github.com/elephantrobotics/elegripper)

![](https://docs.elephantrobotics.com/docs/myGripper-F100-cn/img/git.png)

在电脑终端执行下面命令，安装依赖库

```bash
pip install pyserial
```

### API说明

### get\_firmware\_version()

- **功能:** 获取夹爪固件主版本号
- **参数:** 无
- **返回:** `(int)` 固件主版本号

### get\_modified\_version()

- **功能:** 获取夹爪固件次版本号
- **参数:** 无
- **返回:** `(int)` 固件次版本号

### get\_gripper\_Id()

- **功能:** 获取夹爪ID
- **参数:** 无
- **返回:** `(int)` 夹爪ID

### get\_gripper\_baud()

- **功能:** 获取夹爪波特率
- **参数:** 无
- **返回:**`(int)` 0-5
	- `0`: 115200
		- `1`: 1000000
		- `2`: 57600
		- `3`: 19200
		- `4`: 9600
		- `5`: 4800

### get\_gripper\_value()

- **功能:** 获取夹爪的当前位置数据信息
- **参数:** 无
- **返回:** `(int)` 夹爪的当前位置数据

### get\_gripper\_status()

- **功能:** 获取夹爪的当前状态
- **参数:** 无
- **返回:**`(int)` 0-3
	- `0`: 正在运动
		- `1`: 停止运动，未检测到夹到物体
		- `2`: 停止运动，检测到夹到了物体
		- `3`: 检测到夹到物体以后，物体掉落

### get\_gripper\_speed()

- **功能:** 获取夹爪的当前速度
- **参数:** 无
- **返回:** `(int)` 夹爪的当前速度

### get\_gripper\_P()

- **功能:** 获取夹爪PID的P值
- **参数:** 无
- **返回:** `(int)` 夹爪PID的P值

### get\_gripper\_I()

- **功能:** 获取夹爪PID的I值
- **参数:** 无
- **返回:** `(int)` 夹爪PID的I值

### get\_gripper\_D()

- **功能:** 获取夹爪PID的D值
- **参数:** 无
- **返回:** `(int)` 夹爪PID的D值

### get\_gripper\_cw()

- **功能:** 获取夹爪顺时针可运行误差
- **参数:** 无
- **返回:** `(int)` 夹爪顺时针可运行误差

### get\_gripper\_cww()

- **功能:** 获取夹爪逆时针可运行误差
- **参数:** 无
- **返回:** `(int)` 夹爪逆时针可运行误差

### get\_gripper\_mini\_pressure()

- **功能:** 获取夹爪最小启动力
- **参数:** 无
- **返回:** `(int)` 夹爪最小启动力

### get\_gripper\_io\_open\_value()

- **功能:** 获取夹爪Io张开角度
- **参数:** 无
- **返回:** `(int)` 夹爪Io张开角度

### get\_gripper\_io\_close\_value()

- **功能:** 获取夹爪Io闭合角度
- **参数:** 无
- **返回:** `(int)` 获取夹爪Io闭合角度

### get\_gripper\_queue\_count()

- **功能:** 获取夹爪当前队列的数据量
- **参数:** 无
- **返回:** `(int)` 夹爪当前队列的数据量

### get\_gripper\_vir\_pos()

- **功能:** 获取夹爪舵机虚位数值
- **参数:** 无
- **返回:** `(int)` 夹爪舵机虚位数值

### get\_gripper\_protection\_current()

- **功能:** 获取夹爪夹持电流
- **参数:** 无
- **返回:** `(int)` 夹爪夹持电流

### set\_gripper\_Id(value)

- **功能:** 设置夹爪ID号
- **参数:**
	- `value`: `(int)` 夹爪ID，取值范围 `1-254`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_baud(value)

- **功能:** 设置夹爪波特率
- **参数:**
	- `value`: `(int)` 夹爪波特率，取值范围 `0-5`
		- `0`: 115200
				- `1`: 1000000
				- `2`: 57600
				- `3`: 19200
				- `4`: 9600
				- `5`: 4800
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_enable(value)

- **功能:** 设置夹爪使能状态
- **参数:**
	- `value`: `(int)` 使能状态，取值范围 `0-1`
		- `0`: 掉使能
				- `1`: 上使能
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_value(value,speed)

- **功能:** 设置夹爪以指定的速度转动到指定的位置
- **参数:**
	- `value`: `(int)` 位置，取值范围 `0-100`
		- `speed`: `(int)` 速度，取值范围 `1-100`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_calibration()

- **功能:** 设置夹爪零位校准
- **参数:** 无
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_P(value)

- **功能:** 设置夹爪PID的P值
- **参数:**
	- `value`: `(int)` P值，取值范围 `0-254`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_I(value)

- **功能:** 设置夹爪PID的I值
- **参数:**
	- `value`: `(int)` I值，取值范围 `0-254`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_D(value)

- **功能:** 设置夹爪PID的D值
- **参数:**
	- `value`: `(int)` D值，取值范围 `0-254`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_cw(value)

- **功能:** 设置夹爪顺时针可运行误差
- **参数:**
	- `value`: `(int)` 误差，取值范围 `0-16`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_cww(value)

- **功能:** 设置夹爪逆时针可运行误差
- **参数:**
	- `value`: `(int)` 误差，取值范围 `0-16`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_mini\_pressure(value)

- **功能:** 设置夹爪最小启动力
- **参数:**
	- `value`: `(int)` 最小启动力，取值范围 `0-254`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_torque(value)

- **功能:** 设置夹爪扭矩
- **参数:**
	- `value`: `(int)` 扭矩，取值范围 `0-100`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_output(value)

- **功能:** 设置夹爪IO
- **参数:**
	- `value`: `(int)` 夹爪IO，取值范围 `0-3`
		- `0`: out1 off,out2 off
				- `1`: out1 on,out2 off
				- `2`: out1 off,out2 on
				- `3`: out1 on,out2 on
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_io\_open\_value(value)

- **功能:** 设置夹爪Io张开位置
- **参数:**
	- `value`: `(int)` 位置，取值范围 `0-100`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_io\_close\_value(value)

- **功能:** 设置夹爪Io闭合位置
- **参数:**
	- `value`: `(int)` 位置，取值范围 `0-100`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_speed(speed)

- **功能:** 设置夹爪速度
- **参数:**
	- `speed`: `(int)` 速度，取值范围 `1-100`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_abs\_gripper\_value(value,speed)

- **功能:** 设置夹爪以指定的速度转动到指定的绝对位置
- **参数:**
	- `value`: `(int)` 位置，取值范围 `1-100`
		- `speed`: `(int)` 速度，取值范围 `1-100`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_vir\_pos(value)

- **功能:** 设置夹爪舵机虚位数值
- **参数:**
	- `value`: `(int)` 虚位，取值范围 `0-100`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_protection\_current(value)

- **功能:** 设置夹爪夹持电流
- **参数:**
	- `value`: `(int)` 虚位，取值范围 `1-254`
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_pause()

- **功能:** 设置夹爪暂停运动
- **备注:** 只对set\_abs\_gripper\_value()生效
- **参数:** 无
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_resume()

- **功能:** 设置夹爪恢复运动
- **备注:** 只对set\_abs\_gripper\_value()生效
- **参数:** 无
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

### set\_gripper\_stop()

- **功能:** 设置夹爪停止运动，并清空消息队列
- **备注:** 只对set\_abs\_gripper\_value()生效
- **参数:** 无
- **返回:**`(int)` 0-1
	- `0`: 失败
		- `1`: 成功

#### 测试程序

```python
from elegripper import Gripper
import time
if __name__=="__main__":
    g=Gripper("COM27",baudrate=115200,id=14)##填写实际的串口号和波特率和夹爪ID
    print("夹爪的实际ID为:",g.get_gripper_Id())
    print(g.set_gripper_value(100,100))
    time.sleep(2)
    print(g.set_gripper_value(0,100))
    time.sleep(2)
```