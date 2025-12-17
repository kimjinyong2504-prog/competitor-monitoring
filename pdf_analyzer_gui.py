#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 분석 및 HTML 보고서 생성 - GUI 버전
파일 선택 대화상자를 제공하는 사용자 친화적 인터페이스
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading

# 메인 모듈 import
try:
    from pdf_to_html_report import PDFAnalyzer, LLMAnalyzer, HTMLReportGenerator
except ImportError as e:
    messagebox.showerror("오류", f"필요한 모듈을 찾을 수 없습니다: {e}\n\npdf_to_html_report.py 파일이 같은 폴더에 있는지 확인하세요.")
    sys.exit(1)


class PDFAnalyzerGUI:
    """PDF 분석 GUI 애플리케이션"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PDF to HTML Report Generator")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # 변수
        self.pdf_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.use_local = tk.BooleanVar(value=True)  # 기본값: 로컬 모드
        self.use_api = tk.BooleanVar(value=False)
        self.model_name = tk.StringVar(value="gpt-4o-mini")
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        # 제목
        title_frame = tk.Frame(self.root, bg="#7b64ff", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="PDF 분석 및 HTML 보고서 생성",
            font=("맑은 고딕", 16, "bold"),
            fg="white",
            bg="#7b64ff"
        )
        title_label.pack(pady=15)
        
        # 메인 프레임
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # PDF 파일 선택
        pdf_frame = tk.LabelFrame(main_frame, text="PDF 파일 선택", font=("맑은 고딕", 10, "bold"), padx=10, pady=10)
        pdf_frame.pack(fill=tk.X, pady=10)
        
        pdf_entry = tk.Entry(pdf_frame, textvariable=self.pdf_path, font=("맑은 고딕", 9), width=50)
        pdf_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        pdf_btn = tk.Button(
            pdf_frame,
            text="찾아보기...",
            command=self.select_pdf_file,
            font=("맑은 고딕", 9),
            bg="#7b64ff",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            cursor="hand2"
        )
        pdf_btn.pack(side=tk.RIGHT)
        
        # 출력 파일 설정
        output_frame = tk.LabelFrame(main_frame, text="출력 파일", font=("맑은 고딕", 10, "bold"), padx=10, pady=10)
        output_frame.pack(fill=tk.X, pady=10)
        
        output_entry = tk.Entry(output_frame, textvariable=self.output_path, font=("맑은 고딕", 9), width=50)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        output_btn = tk.Button(
            output_frame,
            text="저장 위치...",
            command=self.select_output_file,
            font=("맑은 고딕", 9),
            bg="#6a54f0",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            cursor="hand2"
        )
        output_btn.pack(side=tk.RIGHT)
        
        # 분석 모드 설정
        mode_frame = tk.LabelFrame(main_frame, text="분석 모드", font=("맑은 고딕", 10, "bold"), padx=10, pady=10)
        mode_frame.pack(fill=tk.X, pady=10)
        
        local_radio = tk.Radiobutton(
            mode_frame,
            text="로컬 모드 (API 키 불필요)",
            variable=self.use_local,
            value=True,
            font=("맑은 고딕", 9),
            command=self.on_mode_change
        )
        local_radio.pack(anchor=tk.W, pady=5)
        
        api_radio = tk.Radiobutton(
            mode_frame,
            text="OpenAI API 모드 (더 정확한 분석)",
            variable=self.use_local,
            value=False,
            font=("맑은 고딕", 9),
            command=self.on_mode_change
        )
        api_radio.pack(anchor=tk.W, pady=5)
        
        # 모델 선택 (API 모드일 때만 표시)
        self.model_frame = tk.Frame(mode_frame)
        self.model_frame.pack(fill=tk.X, padx=20, pady=5)
        
        model_label = tk.Label(self.model_frame, text="모델:", font=("맑은 고딕", 9))
        model_label.pack(side=tk.LEFT)
        
        model_combo = ttk.Combobox(
            self.model_frame,
            textvariable=self.model_name,
            values=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            state="readonly",
            width=20,
            font=("맑은 고딕", 9)
        )
        model_combo.pack(side=tk.LEFT, padx=5)
        self.model_frame.pack_forget()  # 초기에는 숨김
        
        # 진행 상태
        self.progress_frame = tk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=("맑은 고딕", 9),
            fg="#666a73"
        )
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=560
        )
        self.progress_bar.pack(pady=5)
        self.progress_bar.pack_forget()  # 초기에는 숨김
        
        # 실행 버튼
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        self.run_btn = tk.Button(
            button_frame,
            text="분석 시작",
            command=self.start_analysis,
            font=("맑은 고딕", 12, "bold"),
            bg="#12b886",
            fg="white",
            relief=tk.FLAT,
            padx=30,
            pady=10,
            cursor="hand2"
        )
        self.run_btn.pack()
        
    def on_mode_change(self):
        """분석 모드 변경 시"""
        if not self.use_local.get():
            self.model_frame.pack(fill=tk.X, padx=20, pady=5)
            # API 키 확인
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                messagebox.showwarning(
                    "API 키 없음",
                    "OPENAI_API_KEY 환경변수가 설정되지 않았습니다.\n\n"
                    "환경변수를 설정하거나 로컬 모드를 사용하세요."
                )
        else:
            self.model_frame.pack_forget()
    
    def select_pdf_file(self):
        """PDF 파일 선택"""
        filename = filedialog.askopenfilename(
            title="PDF 파일 선택",
            filetypes=[("PDF 파일", "*.pdf"), ("모든 파일", "*.*")]
        )
        if filename:
            self.pdf_path.set(filename)
            # 기본 출력 파일명 설정
            if not self.output_path.get():
                base_name = Path(filename).stem
                output_dir = Path(filename).parent
                self.output_path.set(str(output_dir / f"{base_name}_report.html"))
    
    def select_output_file(self):
        """출력 파일 선택"""
        filename = filedialog.asksaveasfilename(
            title="HTML 보고서 저장",
            defaultextension=".html",
            filetypes=[("HTML 파일", "*.html"), ("모든 파일", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
    
    def start_analysis(self):
        """분석 시작"""
        # 입력 검증
        if not self.pdf_path.get():
            messagebox.showerror("오류", "PDF 파일을 선택하세요.")
            return
        
        if not os.path.exists(self.pdf_path.get()):
            messagebox.showerror("오류", "선택한 PDF 파일을 찾을 수 없습니다.")
            return
        
        if not self.output_path.get():
            messagebox.showerror("오류", "출력 파일 경로를 지정하세요.")
            return
        
        # UI 비활성화
        self.run_btn.config(state=tk.DISABLED)
        self.progress_bar.pack()
        self.progress_bar.start()
        self.progress_label.config(text="PDF 파일을 읽는 중...")
        
        # 별도 스레드에서 분석 실행
        thread = threading.Thread(target=self.run_analysis, daemon=True)
        thread.start()
    
    def run_analysis(self):
        """실제 분석 실행 (별도 스레드)"""
        try:
            pdf_path = self.pdf_path.get()
            output_path = self.output_path.get()
            use_local = self.use_local.get()
            model_name = self.model_name.get()
            
            # 1. PDF 읽기
            self.update_progress("PDF 파일 읽는 중...")
            pdf_analyzer = PDFAnalyzer(pdf_path)
            pdf_text = pdf_analyzer.extract_text()
            metadata = pdf_analyzer.metadata
            
            # 2. 분석
            self.update_progress("PDF 내용 분석 중...")
            llm_analyzer = LLMAnalyzer(use_local=use_local, model_name=model_name)
            analysis_data = llm_analyzer.analyze_pdf_content(pdf_text, metadata)
            
            # 3. HTML 생성
            self.update_progress("HTML 보고서 생성 중...")
            html_generator = HTMLReportGenerator(template_path="automotive.html")
            html_generator.generate_report(analysis_data, output_path=output_path)
            
            # 완료
            self.root.after(0, self.analysis_complete, output_path)
            
        except Exception as e:
            self.root.after(0, self.analysis_error, str(e))
    
    def update_progress(self, message):
        """진행 상태 업데이트"""
        self.root.after(0, lambda: self.progress_label.config(text=message))
    
    def analysis_complete(self, output_path):
        """분석 완료"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_label.config(text="완료!")
        self.run_btn.config(state=tk.NORMAL)
        
        result = messagebox.askyesno(
            "완료",
            f"보고서가 생성되었습니다!\n\n파일: {output_path}\n\n브라우저에서 열까요?"
        )
        
        if result:
            import webbrowser
            webbrowser.open(f"file:///{os.path.abspath(output_path)}")
    
    def analysis_error(self, error_msg):
        """분석 오류"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_label.config(text="오류 발생")
        self.run_btn.config(state=tk.NORMAL)
        
        messagebox.showerror("오류", f"분석 중 오류가 발생했습니다:\n\n{error_msg}")


def main():
    """메인 함수"""
    root = tk.Tk()
    app = PDFAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()











