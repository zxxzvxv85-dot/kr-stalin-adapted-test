# 俄罗斯足球事件配图

源文件为用户提供的《历史转折中的俄罗斯足球.docx》，直接提取其中word/media/image1.png，1024×576。文档及图片SHA-256、完整正文与分页保存在tools/design/RUS_football_20261025.json。

使用原照片，没有AI生成或修复。按已安装KR的report_event_AST_football.png及本项目build_bryukhanov_sketch_event_picture.py规格打包：184×138等比裁切，偏向右侧保留前景门将完整头部；3像素纸边、轻微旋转和阴影，输出210×176透明RGBA PNG。原图保留，不覆盖。

维护：tools/football_event_content.py --write。默认/--check只读检查文本与已登记图片SHA，不重绘。纸边/阴影构造复用既有打包模块；事件图与注册路径均在规格中。

本次没有生成模型、提示词或CLI命令。已检查成品原尺寸，主要球员和前景门将可辨认；游戏引擎最终显示仍待用户验收。
