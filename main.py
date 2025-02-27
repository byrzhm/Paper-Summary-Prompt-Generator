import sys
import re
import pdfplumber
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
)
from PyQt5.QtCore import Qt


class PDFExtractorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setAcceptDrops(True)

    def init_ui(self):
        self.setWindowTitle("PDF Section Extractor")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 拖拽区域
        self.drop_label = QLabel("拖拽PDF文件到这里", self)
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet(
            """
            QLabel {
                border: 4px dashed #aaa;
                padding: 25px;
                font-size: 16px;
                color: #666;
            }
        """
        )
        self.drop_label.setAcceptDrops(True)
        layout.addWidget(self.drop_label)

        # 结果展示区域
        self.result_area = QPlainTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].toLocalFile().lower().endswith(".pdf"):
                event.acceptProposedAction()

    def dropEvent(self, event):
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.process_pdf(file_path)

    def process_pdf(self, file_path):
        try:
            content = extract_sections(file_path)
            self.result_area.setPlainText(content)
            self.drop_label.setText("文件已处理: " + file_path.split("/")[-1])
            self.drop_label.setStyleSheet("border: 4px dashed #4CAF50; color: #666;")
        except Exception as e:
            self.result_area.setPlainText(f"错误: {str(e)}")
            self.drop_label.setStyleSheet("border: 4px dashed #ff0000; color: #666;")

def extract_sections(pdf_path):
    # 提取PDF文本
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.extend(text.split("\n"))

    # 定义需要提取的章节
    sections = {
        "abstract": {
            "pattern": r"^\s*abstract\b",
            "end_marker": r"^\s*(?:\d+\.?\s*)?introduction\b",
            "content": [],
        },
        "introduction": {
            "pattern": r"^\s*(?:\d+\.?\s*)?introduction\b",
            "end_marker": r"^\s*(?:\d+\.?\s*)?(?:related work|methodology|background)\b",
            "content": [],
        },
        "conclusion": {
            "pattern": r"^\s*(?:\d+\.?\s*)?conclusion\b",
            "end_marker": r"^\s*(?:references|bibliography)\b",
            "content": [],
        },
    }

    current_section = None
    end_pattern = None

    for line in full_text:
        # 检查是否开始新章节
        if current_section is None:
            for section, config in sections.items():
                if re.search(config["pattern"], line, re.IGNORECASE):
                    current_section = section
                    end_pattern = re.compile(config["end_marker"], re.IGNORECASE)
                    config["content"].append(line.strip())
                    break
        else:
            # 检查是否到达章节结束
            if end_pattern and end_pattern.search(line):
                current_section = None
                end_pattern = None
            else:
                sections[current_section]["content"].append(line.strip())

    # 生成结果
    result = []
    for section in ["abstract", "introduction", "conclusion"]:
        content = sections[section]["content"]
        if content:
            result.append(f"===== {section.upper()} =====")
            result.append("\n".join(content[1:]))  # 排除标题行
            result.append("\n")
        else:
            result.append(f"===== {section.upper()} NOT FOUND =====")
            result.append("\n")

    return "\n".join(result)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFExtractorApp()
    window.show()
    sys.exit(app.exec_())
