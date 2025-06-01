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
    if font_path is None:
        raise FileNotFoundError("未找到合适的中文字体文件")

    try:
        # 尝试不同的字体大小，确保字符能够适合16x16像素
        font_size = 14
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
                row_data |= (1 << (15 - j))  # 从左到右，高位到低位
        binary_data.append(row_data)

    # 生成C语言代码
    char_code = ord(char)
    char_name = f"char_{char_code:04X}"

    c_code = f"""// CJK字符 '{char}' (Unicode: U+{char_code:04X}) 的16x16单色位图数据
// 生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

#include <stdio.h>
#include <stdint.h>

// 16x16单色帧缓冲区数据 (每行用16位整数表示)
const uint16_t {char_name}_bitmap[16] = {{
"""

    for i, row in enumerate(binary_data):
        c_code += f"    0x{row:04X}"
        if i < 15:
            c_code += ","
        c_code += f"  // 行 {i + 1:2d}: "
        # 添加可视化注释
        for j in range(16):
            if row & (1 << (15 - j)):
                c_code += "█"
            else:
                c_code += "·"
        c_code += "\n"

    c_code += f"""}}; 

// 显示函数
void display_{char_name}() {{
    printf("字符 '{char}' (U+{char_code:04X}) 的16x16位图:\\n");
    printf("┌");
    for(int i = 0; i < 16; i++) printf("─");
    printf("┐\\n");

    for(int row = 0; row < 16; row++) {{
        printf("│");
        for(int col = 0; col < 16; col++) {{
            if({char_name}_bitmap[row] & (1 << (15 - col))) {{
                printf("█");
            }} else {{
                printf(" ");
            }}
        }}
        printf("│\\n");
    }}

    printf("└");
    for(int i = 0; i < 16; i++) printf("─");
    printf("┘\\n");
}}

// 获取指定位置的像素值 (1=黑色, 0=白色)
int get_pixel_{char_name}(int x, int y) {{
    if(x < 0 || x >= 16 || y < 0 || y >= 16) return 0;
    return ({char_name}_bitmap[y] & (1 << (15 - x))) ? 1 : 0;
}}

// 主函数示例
int main() {{
    display_{char_name}();

    // 示例：获取某个像素的值
    printf("\\n像素(8,8)的值: %d\\n", get_pixel_{char_name}(8, 8));

    return 0;
}}
"""

    return c_code

def handle_character(char):
    result = cjk_char_to_c_framebuffer(char)
    print(result)

    with open(f"char_{ord(char):04X}.c", "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\\n代码已保存到文件: char_{ord(char):04X}.c")

# 使用示例
if __name__ == "__main__":
    try:
        text = "中华人民共和国中央人民政府今天成立了！"
        for char in text:
            handle_character(char)

    except Exception as e:
        print(f"错误: {e}")