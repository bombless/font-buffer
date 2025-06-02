import os
from PIL import Image, ImageDraw, ImageFont
import platform


def cjk_char_to_c_framebuffer(char):
    """
    将CJK字符渲染成16x16单色位图，并生成C语言帧缓冲区代码

    参数:
        char (str): 单个CJK字符

    返回:
        str: C语言程序代码
    """

    # 检查输入是否为单个字符
    if len(char) != 1:
        raise ValueError("输入必须是单个字符")

    def get_consolas_font_path():
        if platform.system() != "Windows":
            # 非Windows系统的备用字体路径
            fallback_paths = [
                "/System/Library/Fonts/STSong.ttc",  # macOS
                "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",  # Linux
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"  # Linux备用
            ]
            for path in fallback_paths:
                if os.path.exists(path):
                    return path
            return None

        # Windows系统宋体路径
        font_paths = [
            "C:\Windows\Fonts\consola.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/SimSun.ttf",
            "C:/Windows/Fonts/simhei.ttf"  # 备用黑体
        ]

        for path in font_paths:
            if os.path.exists(path):
                return path
        return None
    # 获取Windows系统中的宋体字体路径
    def get_simsun_font_path():
        if platform.system() != "Windows":
            # 非Windows系统的备用字体路径
            fallback_paths = [
                "/System/Library/Fonts/STSong.ttc",  # macOS
                "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",  # Linux
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"  # Linux备用
            ]
            for path in fallback_paths:
                if os.path.exists(path):
                    return path
            return None

        # Windows系统宋体路径
        font_paths = [
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/SimSun.ttf",
            "C:/Windows/Fonts/simhei.ttf"  # 备用黑体
        ]

        for path in font_paths:
            if os.path.exists(path):
                return path
        return None

    # 获取字体
    font_path = get_simsun_font_path()
    digits_font_path = get_consolas_font_path()
    if font_path is None:
        raise FileNotFoundError("未找到合适的中文字体文件")

    try:
        # 尝试不同的字体大小，确保字符能够适合16x16像素
        font_size = 14
        if ord(char) < 128:
            font = ImageFont.truetype(digits_font_path, font_size)
        else:

            font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        raise Exception(f"无法加载字体文件: {e}")

    # 创建16x16的图像
    img = Image.new('L', (16, 16), color=255)  # 白色背景
    draw = ImageDraw.Draw(img)

    # 获取字符的边界框来居中显示
    try:
        bbox = draw.textbbox((0, 0), char, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 计算居中位置
        x = (16 - text_width) // 2 - bbox[0]
        y = (16 - text_height) // 2 - bbox[1]

        # 绘制字符
        draw.text((x, y), char, font=font, fill=0)  # 黑色字符
    except Exception as e:
        # 如果获取边界框失败，使用默认位置
        draw.text((2, 1), char, font=font, fill=0)

    # 转换为单色位图数据
    pixels = list(img.getdata())

    # 将灰度值转换为二进制（阈值128）
    binary_data = []
    for i in range(16):  # 16行
        row_data = 0
        for j in range(16):  # 16列
            pixel_value = pixels[i * 16 + j]
            if pixel_value < 128:  # 黑色像素
                row_data |= (1 << j)  # 从左到右，高位到低位
        binary_data.append(row_data)
    return binary_data

def generate_file(lst):
    # 生成C语言代码


    c_code = """#include "freertos/FreeRTOS.h"
#define DECL_CHARACTER(name, ...) \\
    static const uint16_t char_##name##_bitmap[16] = __VA_ARGS__; \\
    case 0x##name: \\
        return char_##name##_bitmap;

const uint16_t* character_get_bitmap(uint16_t character) {
    switch (character) {
"""
    for char_code, binary_data in lst:
        c_code += f"""        DECL_CHARACTER({char_code:04X}, """
        c_code += "{\n"
        for i, row in enumerate(binary_data):
            c_code += f"            0x{row:04X}"
            if i < 15:
                c_code += ","
            c_code += f"  // 行 {i + 1:2d}: "
            # 添加可视化注释
            for j in range(16):
                if row & (1 << j):
                    c_code += "█"
                else:
                    c_code += "·"
            c_code += "\n"
        c_code += "        })\n"
    c_code += """
        default:
            return NULL;
    }
}
"""


    with open("characters.c", "w", encoding="utf-8") as f:
        f.write(c_code)

# 使用示例
if __name__ == "__main__":
    try:
        text = "中华人民共和国中央人民政府今天成立了！0123456789."
        lst = []
        s = set()
        for char in text:
            if char in s:
                continue
            s.add(char)
            binary_data = cjk_char_to_c_framebuffer(char)
            lst.append((ord(char), binary_data))
        generate_file(lst)

    except Exception as e:
        print(f"错误: {e}")